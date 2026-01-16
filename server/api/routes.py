from flask import jsonify, request
from functools import wraps
from . import api_bp
from services.trial_manager import TrialManager
from services.license_manager import LicenseManager
from services.email_service import EmailService
from services.rate_limiter import rate_limiter
from services.validation import validate_email, validate_license_key, validate_hardware_id, sanitize_string
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

trial_manager = TrialManager()
license_manager = LicenseManager()
email_service = EmailService()


def require_admin_key(f):
    """
    Decorator to require admin API key for protected endpoints.
    
    Checks X-Admin-Key header against ADMIN_API_KEY from environment.
    Returns 401 Unauthorized if key is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = Config.ADMIN_API_KEY
        provided_key = request.headers.get('X-Admin-Key')
        
        if not admin_key:
            logger.warning("ADMIN_API_KEY not configured - admin endpoint disabled")
            return jsonify({'success': False, 'error': 'admin_not_configured'}), 503
        
        if not provided_key:
            logger.warning(f"Admin endpoint access without key from IP: {request.remote_addr}")
            return jsonify({'success': False, 'error': 'unauthorized', 'message': 'Admin key required'}), 401
        
        # Use constant-time comparison to prevent timing attacks
        import hmac
        if not hmac.compare_digest(provided_key, admin_key):
            logger.warning(f"Invalid admin key attempt from IP: {request.remote_addr}")
            return jsonify({'success': False, 'error': 'unauthorized', 'message': 'Invalid admin key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "online", "version": "1.0.0"})

@api_bp.route('/trial/check', methods=['POST'])
def check_trial():
    data = request.get_json()
    if not data or 'hardware_id' not in data:
        return jsonify({"error": "Missing hardware_id"}), 400
        
    result = trial_manager.check_trial(data['hardware_id'])
    return jsonify(result)

@api_bp.route('/trial/increment', methods=['POST'])
def increment_trial():
    data = request.get_json()
    if not data or 'hardware_id' not in data:
        return jsonify({"error": "Missing hardware_id"}), 400
    
    files_count = data.get('files_count', 1)
    result = trial_manager.increment_trial(data['hardware_id'], files_count)
    return jsonify(result)

@api_bp.route('/trial/reset', methods=['POST'])
def reset_trial():
    data = request.get_json()
    if not data or 'hardware_id' not in data:
        return jsonify({"error": "Missing hardware_id"}), 400
        
    result = trial_manager.reset_trial(data['hardware_id'])
    return jsonify(result)

@api_bp.route('/license/validate', methods=['POST'])
def validate_license():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'no_data'}), 400
    
    # Validate inputs
    email_result = validate_email(data.get('email', ''))
    if not email_result['valid']:
        return jsonify({'success': False, 'error': email_result['error'], 'message': email_result['message']}), 400
    
    key_result = validate_license_key(data.get('license_key', ''))
    if not key_result['valid']:
        return jsonify({'success': False, 'error': key_result['error'], 'message': key_result['message']}), 400
    
    hw_result = validate_hardware_id(data.get('hardware_id', ''))
    if not hw_result['valid']:
        return jsonify({'success': False, 'error': hw_result['error'], 'message': hw_result['message']}), 400
    
    device_name = sanitize_string(data.get('device_name', 'Unknown Device'), max_length=100)
    
    result = license_manager.validate_license(
        email_result['email'], 
        key_result['license_key'], 
        hw_result['hardware_id'], 
        device_name
    )
    
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@api_bp.route('/license/transfer', methods=['POST'])
def transfer_license():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'no_data'}), 400
    
    # Validate inputs
    email_result = validate_email(data.get('email', ''))
    if not email_result['valid']:
        return jsonify({'success': False, 'error': email_result['error'], 'message': email_result['message']}), 400
    
    key_result = validate_license_key(data.get('license_key', ''))
    if not key_result['valid']:
        return jsonify({'success': False, 'error': key_result['error'], 'message': key_result['message']}), 400
    
    hw_result = validate_hardware_id(data.get('new_hardware_id', ''))
    if not hw_result['valid']:
        return jsonify({'success': False, 'error': hw_result['error'], 'message': hw_result['message']}), 400
    
    new_device_name = sanitize_string(data.get('new_device_name', 'Unknown Device'), max_length=100)
    
    result = license_manager.transfer_license(
        email_result['email'], 
        key_result['license_key'], 
        hw_result['hardware_id'], 
        new_device_name
    )
    
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@api_bp.route('/license/create', methods=['POST'])
@require_admin_key
def create_license():
    """Create a new license - ADMIN ONLY endpoint"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'no_data'}), 400
    
    # Validate email
    email_result = validate_email(data.get('email', ''))
    if not email_result['valid']:
        return jsonify({'success': False, 'error': email_result['error'], 'message': email_result['message']}), 400
    
    customer_name = sanitize_string(data.get('customer_name', ''), max_length=100)
    expires_days = data.get('expires_days', 365)
    
    # Validate expires_days
    if not isinstance(expires_days, int) or expires_days < 1 or expires_days > 3650:
        return jsonify({'success': False, 'error': 'invalid_expires_days', 'message': 'expires_days must be 1-3650'}), 400
    
    license_key = license_manager.create_license(email_result['email'], customer_name, expires_days)
    
    if license_key:
        logger.info(f"Admin created license for {email_result['email']}")
        return jsonify({
            'success': True,
            'license_key': license_key,
            'email': email_result['email'],
            'expires_days': expires_days
        })
    else:
        return jsonify({'success': False, 'error': 'creation_failed'}), 500

@api_bp.route('/license/forgot', methods=['POST'])
def forgot_license():
    """Find and return a license key for a user who forgot it"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'no_data'}), 400
    
    # Validate email
    email_result = validate_email(data.get('email', ''))
    if not email_result['valid']:
        return jsonify({'success': False, 'error': email_result['error'], 'message': email_result['message']}), 400
    
    email = email_result['email']  # Use validated/normalized email
    
    # Rate limiting check
    ip_address = request.remote_addr
    rate_check = rate_limiter.check_rate_limit('forgot_license', email=email, ip_address=ip_address)
    
    if not rate_check['allowed']:
        return jsonify({
            'success': False,
            'error': 'rate_limit_exceeded',
            'message': rate_check['message'],
            'retry_after': rate_check['retry_after']
        }), 429  # HTTP 429 Too Many Requests
    
    result = license_manager.find_license_by_email(email)
    
    if result.get('success'):
        # Send email with recovered license key
        license_key = result.get('license_key')
        try:
            email_sent = email_service.send_forgot_license_email(email, license_key)
            if not email_sent:
                logger.warning(f"Failed to send forgot license email to {email} - check SMTP configuration")
            else:
                logger.info(f"Forgot license email successfully sent to {email}")
        except Exception as e:
            logger.error(f"Exception sending forgot license email to {email}: {e}")
        
        # Remove license_key from response - only send via email
        result = {
            'success': True,
            'message': 'License key sent to your email',
            'email_sent': email_sent if 'email_sent' in locals() else False
        }
    
    status_code = 200 if result.get('success') else 404 if result.get('error') == 'no_license_found' else 400
    return jsonify(result), status_code
@api_bp.route('/trial/create', methods=['POST'])
def create_trial():
    """Create a trial license for a user"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'no_data'}), 400
    
    email = data.get('email')
    hardware_id = data.get('hardware_id')
    device_name = data.get('device_name', 'Unknown Device')
    
    if not all([email, hardware_id]):
        return jsonify({'success': False, 'error': 'missing_parameters'}), 400
    
    # Rate limiting check (very strict for trials)
    ip_address = request.remote_addr
    rate_check = rate_limiter.check_rate_limit('trial_create', email=email, ip_address=ip_address, hardware_id=hardware_id)
    
    if not rate_check['allowed']:
        return jsonify({
            'success': False,
            'error': 'rate_limit_exceeded',
            'message': rate_check['message'],
            'retry_after': rate_check['retry_after']
        }), 429  # HTTP 429 Too Many Requests
    
    result = license_manager.create_trial_license(email, hardware_id, device_name)
    
    if result.get('success'):
        # Send trial email to user
        license_key = result.get('license_key')
        try:
            email_sent = email_service.send_trial_email(email, license_key)
            if not email_sent:
                logger.warning(f"Failed to send trial email to {email} - check SMTP configuration")
            else:
                logger.info(f"Trial email successfully sent to {email}")
        except Exception as e:
            logger.error(f"Exception sending trial email to {email}: {e}")
    
    status_code = 201 if result.get('success') else 400
    return jsonify(result), status_code

@api_bp.route('/trial/check-eligibility', methods=['POST'])
def check_trial_eligibility():
    """Check if a user is eligible for a trial"""
    data = request.get_json()
    if not data:
        return jsonify({'eligible': False, 'error': 'no_data'}), 400
    
    email = data.get('email')
    hardware_id = data.get('hardware_id')
    
    if not all([email, hardware_id]):
        return jsonify({'eligible': False, 'error': 'missing_parameters'}), 400
    
    result = license_manager.check_trial_eligibility(email, hardware_id)
    
    status_code = 200
    return jsonify(result), status_code


@api_bp.route('/trial/status', methods=['GET', 'POST'])
def trial_status():
    """Get trial status for a license key"""
    if request.method == 'POST':
        data = request.get_json()
        license_key = data.get('license_key') if data else None
    else:
        license_key = request.args.get('license_key')
    
    if not license_key:
        return jsonify({'error': 'missing_license_key'}), 400
    
    result = license_manager.check_trial_status(license_key)
    
    if 'error' in result:
        return jsonify(result), 404
    
    return jsonify(result), 200

# ============================================================================
# ADMIN ENDPOINTS - PLATFORM MIGRATION
# ============================================================================

@api_bp.route('/admin/migrate-platforms', methods=['POST'])
@require_admin_key
def admin_migrate_platforms():
    """
    Migrate existing licenses to include platform field.
    
    This is a one-time operation to update licenses created before
    multi-platform support was added. Safe to run multiple times.
    
    ADMIN ONLY - Requires X-Admin-Key header
    """
    try:
        result = license_manager.migrate_existing_licenses_platform()
        
        logger.info(f"Platform migration completed: {result}")
        
        return jsonify({
            'success': True,
            'migration_result': result,
            'message': f"Migrated {result['migrated']} licenses, {result['already_migrated']} already had platform, {result['errors']} errors"
        }), 200
        
    except Exception as e:
        logger.error(f"Platform migration failed: {e}")
        return jsonify({
            'success': False,
            'error': 'migration_failed',
            'message': str(e)
        }), 500


@api_bp.route('/admin/platform-stats', methods=['GET'])
@require_admin_key
def admin_platform_stats():
    """
    Get statistics about licenses by platform.
    
    ADMIN ONLY - Requires X-Admin-Key header
    """
    try:
        from services.license_manager import Platform
        
        stats = {
            'total': 0,
            'by_platform': {},
            'no_platform': 0
        }
        
        licenses = license_manager.load_licenses()
        
        for license_key, license_data in licenses.items():
            stats['total'] += 1
            platform = license_data.get('platform')
            
            if platform:
                stats['by_platform'][platform] = stats['by_platform'].get(platform, 0) + 1
            else:
                stats['no_platform'] += 1
        
        return jsonify({
            'success': True,
            'stats': stats,
            'platforms_available': Platform.all_values()
        }), 200
        
    except Exception as e:
        logger.error(f"Platform stats failed: {e}")
        return jsonify({
            'success': False,
            'error': 'stats_failed',
            'message': str(e)
        }), 500


@api_bp.route('/admin/find-by-platform', methods=['GET'])
@require_admin_key
def admin_find_by_platform():
    """
    Find all licenses from a specific platform.
    
    Query params:
        platform: Platform name ('gumroad', 'msstore', etc.)
    
    ADMIN ONLY - Requires X-Admin-Key header
    """
    try:
        platform = request.args.get('platform')
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'missing_platform',
                'message': 'Platform query parameter required'
            }), 400
        
        licenses = license_manager.find_licenses_by_platform(platform)
        
        # Sanitize output (don't expose full hardware IDs)
        sanitized = {}
        for key, data in licenses.items():
            sanitized[key] = {
                'email': data.get('email'),
                'platform': data.get('platform'),
                'is_active': data.get('is_active'),
                'created_date': data.get('created_date'),
                'expiry_date': data.get('expiry_date'),
            }
        
        return jsonify({
            'success': True,
            'platform': platform,
            'count': len(sanitized),
            'licenses': sanitized
        }), 200
        
    except Exception as e:
        logger.error(f"Find by platform failed: {e}")
        return jsonify({
            'success': False,
            'error': 'lookup_failed',
            'message': str(e)
        }), 500