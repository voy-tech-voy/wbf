"""
Input Validation Utilities

Provides robust validation for emails, license keys, and other inputs.
"""

import re
import string


# RFC 5322 compliant email regex (simplified but robust)
# Handles most common email formats without being overly strict
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?'
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)+$'
)

# Common disposable email domains to block
DISPOSABLE_EMAIL_DOMAINS = {
    'tempmail.com', 'throwaway.email', '10minutemail.com',
    'guerrillamail.com', 'mailinator.com', 'temp-mail.org',
    'fakeinbox.com', 'trashmail.com', 'sharklasers.com',
    'getnada.com', 'maildrop.cc', 'dispostable.com'
}

# License key format: XXXX-XXXX-XXXX-XXXX (alphanumeric groups)
LICENSE_KEY_REGEX = re.compile(
    r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
)


def validate_email(email: str, allow_disposable: bool = False) -> dict:
    """
    Validate an email address.
    
    Args:
        email: Email address to validate
        allow_disposable: Whether to allow disposable email addresses
        
    Returns:
        dict with 'valid' (bool), 'email' (normalized), 'error' (if invalid)
    """
    if not email:
        return {
            'valid': False,
            'error': 'email_required',
            'message': 'Email address is required'
        }
    
    # Normalize
    email = email.strip().lower()
    
    # Length check
    if len(email) > 254:  # RFC 5321 limit
        return {
            'valid': False,
            'error': 'email_too_long',
            'message': 'Email address is too long'
        }
    
    if len(email) < 5:  # Minimum: a@b.c
        return {
            'valid': False,
            'error': 'email_too_short',
            'message': 'Email address is too short'
        }
    
    # Format check
    if not EMAIL_REGEX.match(email):
        return {
            'valid': False,
            'error': 'invalid_email_format',
            'message': 'Please enter a valid email address'
        }
    
    # Extract domain
    domain = email.split('@')[1]
    
    # Check for disposable emails
    if not allow_disposable and domain in DISPOSABLE_EMAIL_DOMAINS:
        return {
            'valid': False,
            'error': 'disposable_email',
            'message': 'Please use a non-disposable email address'
        }
    
    return {
        'valid': True,
        'email': email,
        'domain': domain
    }


def validate_license_key(license_key: str) -> dict:
    """
    Validate a license key format.
    
    Args:
        license_key: License key to validate
        
    Returns:
        dict with 'valid' (bool), 'license_key' (normalized), 'error' (if invalid)
    """
    if not license_key:
        return {
            'valid': False,
            'error': 'license_key_required',
            'message': 'License key is required'
        }
    
    # Normalize: uppercase, strip whitespace
    license_key = license_key.strip().upper()
    
    # Check format
    if not LICENSE_KEY_REGEX.match(license_key):
        return {
            'valid': False,
            'error': 'invalid_license_format',
            'message': 'Invalid license key format. Expected: XXXX-XXXX-XXXX-XXXX'
        }
    
    return {
        'valid': True,
        'license_key': license_key
    }


def validate_hardware_id(hardware_id: str) -> dict:
    """
    Validate a hardware ID.
    
    Args:
        hardware_id: Hardware ID to validate
        
    Returns:
        dict with 'valid' (bool), 'hardware_id' (str), 'error' (if invalid)
    """
    if not hardware_id:
        return {
            'valid': False,
            'error': 'hardware_id_required',
            'message': 'Hardware ID is required'
        }
    
    # Normalize
    hardware_id = hardware_id.strip()
    
    # Length check (hardware IDs are typically hashes)
    if len(hardware_id) < 8:
        return {
            'valid': False,
            'error': 'hardware_id_too_short',
            'message': 'Invalid hardware ID'
        }
    
    if len(hardware_id) > 128:
        return {
            'valid': False,
            'error': 'hardware_id_too_long',
            'message': 'Invalid hardware ID'
        }
    
    # Character check - should be alphanumeric (hex) or contain hyphens
    valid_chars = set(string.hexdigits + '-')
    if not all(c in valid_chars for c in hardware_id):
        return {
            'valid': False,
            'error': 'hardware_id_invalid_chars',
            'message': 'Invalid hardware ID format'
        }
    
    return {
        'valid': True,
        'hardware_id': hardware_id
    }


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize a string input by stripping and truncating.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ''
    return str(value).strip()[:max_length]
