"""
Rate Limiting Service for API Protection
Implements industry-standard rate limiting to prevent abuse and DDoS attacks
"""

import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with sliding window
    
    Security measures implemented:
    1. IP-based rate limiting
    2. Email-based rate limiting
    3. Hardware ID tracking
    4. Exponential backoff
    5. Sliding window algorithm
    """
    
    def __init__(self):
        # Rate limit storage: {identifier: {'requests': [(timestamp, count)], 'blocked_until': timestamp}}
        self.requests = defaultdict(lambda: {'requests': [], 'blocked_until': None, 'violation_count': 0})
        
        # Rate limit configurations (industry standards)
        self.limits = {
            'trial_create': {
                'max_requests': 3,      # Max 3 trials per window
                'window_seconds': 86400,  # 24 hour window
                'block_duration': 3600    # Block for 1 hour after limit
            },
            'forgot_license': {
                'max_requests': 5,       # Max 5 forgot requests per window
                'window_seconds': 3600,   # 1 hour window
                'block_duration': 1800    # Block for 30 minutes
            },
            'login_validate': {
                'max_requests': 10,      # Max 10 login attempts per window
                'window_seconds': 600,    # 10 minute window
                'block_duration': 900     # Block for 15 minutes
            }
        }
        
        # Cleanup old entries every 1000 checks
        self.check_counter = 0
    
    def _generate_identifier(self, email=None, ip_address=None, hardware_id=None):
        """Generate unique identifier from multiple factors"""
        parts = []
        if email:
            parts.append(f"email:{email.lower()}")
        if ip_address:
            parts.append(f"ip:{ip_address}")
        if hardware_id:
            parts.append(f"hw:{hardware_id}")
        
        identifier = "|".join(parts)
        # Hash for privacy
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def _cleanup_old_requests(self):
        """Remove old request records to prevent memory leak"""
        current_time = time.time()
        max_age = 86400  # Keep records for 24 hours max
        
        for identifier in list(self.requests.keys()):
            data = self.requests[identifier]
            # Remove requests older than max_age
            data['requests'] = [
                (ts, count) for ts, count in data['requests']
                if current_time - ts < max_age
            ]
            # Remove empty entries
            if not data['requests'] and not data['blocked_until']:
                del self.requests[identifier]
    
    def check_rate_limit(self, action, email=None, ip_address=None, hardware_id=None):
        """
        Check if request should be allowed
        
        Args:
            action: 'trial_create', 'forgot_license', or 'login_validate'
            email: User email
            ip_address: Request IP address
            hardware_id: Hardware identifier
        
        Returns:
            dict: {'allowed': bool, 'reason': str, 'retry_after': int}
        """
        # Cleanup periodically
        self.check_counter += 1
        if self.check_counter % 1000 == 0:
            self._cleanup_old_requests()
        
        if action not in self.limits:
            logger.warning(f"Unknown rate limit action: {action}")
            return {'allowed': True, 'reason': 'unknown_action'}
        
        limit_config = self.limits[action]
        identifier = self._generate_identifier(email, ip_address, hardware_id)
        current_time = time.time()
        
        data = self.requests[identifier]
        
        # Check if currently blocked
        if data['blocked_until'] and current_time < data['blocked_until']:
            retry_after = int(data['blocked_until'] - current_time)
            logger.warning(
                f"Rate limit block active for {action}: "
                f"email={email}, retry_after={retry_after}s"
            )
            return {
                'allowed': False,
                'reason': 'rate_limit_exceeded',
                'retry_after': retry_after,
                'message': f'Too many requests. Please try again in {retry_after} seconds.'
            }
        
        # Clear block if expired
        if data['blocked_until'] and current_time >= data['blocked_until']:
            data['blocked_until'] = None
            data['violation_count'] = 0
        
        # Remove old requests outside the window
        window_start = current_time - limit_config['window_seconds']
        data['requests'] = [
            (ts, count) for ts, count in data['requests']
            if ts >= window_start
        ]
        
        # Count requests in current window
        request_count = sum(count for ts, count in data['requests'])
        
        # Check if limit exceeded
        if request_count >= limit_config['max_requests']:
            # Block user
            data['violation_count'] += 1
            # Exponential backoff: double block time for repeat offenders
            block_multiplier = min(2 ** (data['violation_count'] - 1), 8)
            block_duration = limit_config['block_duration'] * block_multiplier
            data['blocked_until'] = current_time + block_duration
            
            logger.warning(
                f"Rate limit exceeded for {action}: "
                f"email={email}, ip={ip_address}, hw={hardware_id}, "
                f"count={request_count}, violations={data['violation_count']}, "
                f"blocked_for={block_duration}s"
            )
            
            return {
                'allowed': False,
                'reason': 'rate_limit_exceeded',
                'retry_after': int(block_duration),
                'message': f'Too many requests. Blocked for {int(block_duration/60)} minutes.'
            }
        
        # Allow request and record it
        data['requests'].append((current_time, 1))
        remaining = limit_config['max_requests'] - request_count - 1
        
        logger.info(
            f"Rate limit check passed for {action}: "
            f"email={email}, remaining={remaining}/{limit_config['max_requests']}"
        )
        
        return {
            'allowed': True,
            'reason': 'ok',
            'remaining': remaining,
            'reset_after': limit_config['window_seconds']
        }
    
    def record_request(self, action, email=None, ip_address=None, hardware_id=None):
        """Record a request (called after successful processing)"""
        identifier = self._generate_identifier(email, ip_address, hardware_id)
        # Already recorded in check_rate_limit
        pass
    
    def reset_limit(self, email=None, ip_address=None, hardware_id=None):
        """Admin function to reset rate limit for a user"""
        identifier = self._generate_identifier(email, ip_address, hardware_id)
        if identifier in self.requests:
            del self.requests[identifier]
            logger.info(f"Rate limit reset for: email={email}, ip={ip_address}, hw={hardware_id}")
            return True
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()
