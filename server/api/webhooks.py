from flask import jsonify, request
from . import webhook_bp
from services.license_manager import LicenseManager
from services.email_service import EmailService
import logging
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)
license_manager = LicenseManager()
email_service = EmailService()

# Webhook debug log file
WEBHOOK_DEBUG_LOG = 'webhook_debug.jsonl'

# Map Gumroad Product Permalinks/IDs to duration in days
PRODUCT_DURATIONS = {
    "imgwave": 30,  # Default to 30 days (will be overridden by variant tier)
    "free_trial_3h": 0.125,
    "daily_sub": 1,
    "monthly_sub": 30,
    "yearly_sub": 365,
    "lifetime_deal": 36500,
}

# Map Gumroad variant tiers to duration in days
TIER_DURATIONS = {
    "Pricing": 30,  # Default tier from your product (when no explicit tier)
    "Monthly": 30,
    "Yearly": 365,
    "Lifetime": 36500,  # ~100 years
    "3-Month": 90,
    "6-Month": 180,
}

def normalize_gumroad_purchase(data, duration_days, tier):
    """
    Normalize Gumroad webhook data into standardized purchase_info structure.
    This allows future payment providers (Stripe, direct sales, etc) to use the same format.
    
    Args:
        data: Raw Gumroad webhook POST data
        duration_days: Calculated license duration based on tier/product
        tier: Calculated tier (e.g., 'Lifetime', 'Monthly')
    
    Returns:
        dict: Standardized purchase_info structure
    """
    purchase_date = data.get('sale_timestamp', datetime.utcnow().isoformat())
    is_recurring = data.get('recurrence') == 'monthly' or data.get('subscription_id') is not None
    
    purchase_info = {
        'source': 'gumroad',
        'source_license_key': data.get('license_key'),
        'sale_id': data.get('sale_id'),
        'customer_id': data.get('purchaser_id'),
        'product_id': data.get('product_id'),
        'product_name': data.get('product_name', ''),
        'tier': tier,  # Use calculated tier, not raw webhook data
        'price': data.get('price'),
        'currency': data.get('currency', 'usd').lower(),
        'purchase_date': purchase_date,
        'is_recurring': is_recurring,
        'recurrence': data.get('recurrence'),
        'subscription_id': data.get('subscription_id'),
        'renewal_date': None,  # Calculate if recurring
        'is_refunded': data.get('refunded') == 'true',
        'refund_date': None,  # Not provided by Gumroad in webhook
        'is_disputed': data.get('disputed') == 'true',
        'is_test': data.get('test') == 'true'
    }
    
    return purchase_info

def save_webhook_log(data, status, response):
    """Save raw webhook data to file for debugging"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "raw_data": dict(data),
        "response": response
    }
    
    try:
        with open('webhook_logs.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        logger.info(f"Webhook logged to webhook_logs.jsonl")
    except Exception as e:
        logger.error(f"Failed to save webhook log: {e}")

@webhook_bp.route('/gumroad', methods=['POST'])
def gumroad_webhook():
    """Handle Gumroad purchase webhooks"""
    
    # Try to get data from form first, then JSON
    data = request.form.to_dict() if request.form else request.get_json() or {}
    
    if not data:
        error_response = {"error": "No data received"}
        save_webhook_log({}, "error", error_response)
        return jsonify(error_response), 400
    
    # Log raw webhook data (IMPORTANT FOR DEBUGGING)
    logger.info(f"Raw Gumroad webhook received: {json.dumps(data, indent=2)}")
    
    # Extract customer info
    email = data.get('email')
    product_permalink = data.get('permalink', '')
    product_name = data.get('product_name', '')
    gumroad_license_key = data.get('license_key')
    sale_id = data.get('sale_id')
    
    # Extract tier/variant if available (Gumroad sends as variants[Tier])
    tier = data.get('variants[Tier]', '')
    
    # If no tier specified, default to Lifetime for this product
    if not tier:
        tier = 'Lifetime'
    
    # Log all extracted fields for debugging
    logger.info(f"Extracted fields - Email: {email}, Product: {product_permalink}, Tier: {tier}, License Key: {gumroad_license_key}, Sale ID: {sale_id}")
    
    # Basic validation
    if not email:
        error_response = {"error": "Email required"}
        save_webhook_log(data, "error", error_response)
        return jsonify(error_response), 400
    
    # CHECK FOR REFUND: If this is a refund webhook (refunded=true),
    # find and deactivate the license instead of creating a new one
    if data.get('refunded') == 'true':
        logger.info(f"Refund detected for license key {gumroad_license_key}")
        
        # Find our license by the Gumroad license key
        our_license_key = license_manager.find_license_by_source_key(gumroad_license_key)
        
        if our_license_key:
            refund_result = license_manager.handle_refund(our_license_key, 'gumroad_refund')
            response = {
                "status": "refund_processed",
                "our_license_key": our_license_key,
                "gumroad_license_key": gumroad_license_key,
                "message": "License refunded and deactivated"
            }
            save_webhook_log(data, "refund_success", response)
            logger.info(f"Successfully processed refund for {our_license_key}")
            return jsonify(response), 200
        else:
            error_response = {
                "status": "refund_failed",
                "error": "License not found",
                "gumroad_license_key": gumroad_license_key
            }
            save_webhook_log(data, "refund_failed", error_response)
            logger.warning(f"Refund webhook received but license not found for {gumroad_license_key}")
            return jsonify(error_response), 404
    
    # PURCHASE: If not a refund, process as new purchase
    # Determine duration based on tier first, then product
    # Priority: tier variant > product permalink > default
    if tier and tier in TIER_DURATIONS:
        duration_days = TIER_DURATIONS[tier]
        logger.info(f"Mapped tier '{tier}' to {duration_days} days")
    else:
        duration_days = PRODUCT_DURATIONS.get(product_permalink, 365)
        logger.info(f"Mapped product '{product_permalink}' to {duration_days} days")
    
    # Normalize Gumroad data into standardized purchase_info structure
    purchase_info = normalize_gumroad_purchase(data, duration_days, tier)
    
    logger.info(f"Normalized purchase info: {json.dumps(purchase_info, indent=2)}")
    
    # Create License with structured purchase_info
    try:
        license_key = license_manager.create_license(
            email=email,
            expires_days=int(duration_days),
            license_key=None,
            purchase_info=purchase_info
        )
        
        if license_key:
            # Send Email
            email_sent = email_service.send_license_email(email, license_key, None)
            
            response = {
                "status": "success", 
                "license_key": license_key,
                "email_sent": email_sent
            }
            save_webhook_log(data, "success", response)
            logger.info(f"License created successfully for {email}")
            
            return jsonify(response), 200
        else:
            error_response = {"error": "Failed to create license"}
            save_webhook_log(data, "error", error_response)
            return jsonify(error_response), 500
            
    except Exception as e:
        logger.error(f"Exception processing webhook: {str(e)}", exc_info=True)
        error_response = {"error": str(e)}
        save_webhook_log(data, "exception", error_response)
        return jsonify(error_response), 500

@webhook_bp.route('/gumroad/test-refund', methods=['POST'])
def gumroad_test_refund():
    """
    TESTING ENDPOINT - Logs ALL webhook data for diagnostic purposes
    Gumroad sends refunds as updates to the purchase webhook with refunded=true flag
    This endpoint captures that data for testing
    Endpoint: POST /api/v1/webhooks/gumroad/test-refund
    """
    
    # Capture everything Gumroad sends
    data = request.form.to_dict() if request.form else request.get_json() or {}
    
    debug_record = {
        'timestamp': datetime.utcnow().isoformat(),
        'endpoint': 'test-refund',
        'method': request.method,
        'content_type': request.content_type,
        'all_form_data': dict(request.form) if request.form else {},
        'all_json_data': request.get_json() if request.is_json else {},
        'raw_data': data,
        'headers': dict(request.headers),
    }
    
    # Log to debug file
    try:
        with open(WEBHOOK_DEBUG_LOG, 'a') as f:
            f.write(json.dumps(debug_record, default=str) + '\n')
        logger.info(f"Test webhook logged - check {WEBHOOK_DEBUG_LOG}")
    except Exception as e:
        logger.error(f"Failed to log test webhook: {e}")
    
    return jsonify({
        "status": "debug_logged",
        "message": f"Webhook data logged to {WEBHOOK_DEBUG_LOG}",
        "received_fields": list(data.keys()),
        "data_sample": {k: v for k, v in list(data.items())[:5]}
    }), 200

@webhook_bp.route('/gumroad/webhook-logs', methods=['GET'])
def gumroad_webhook_logs():
    """
    View diagnostic webhook logs
    Shows ALL webhooks received (purchases and refunds with refunded=true flag)
    """
    try:
        logs = []
        
        # Read from webhook_debug.jsonl (detailed logs)
        if os.path.exists(WEBHOOK_DEBUG_LOG):
            with open(WEBHOOK_DEBUG_LOG, 'r') as f:
                for line in f.readlines()[-50:]:  # Last 50 entries
                    try:
                        logs.append(json.loads(line))
                    except:
                        pass
        
        return jsonify({
            "total_logs": len(logs),
            "logs": logs,
            "instructions": {
                "step_1": "Use test endpoint to send data",
                "step_2": "POST to /api/v1/webhooks/gumroad/test-refund",
                "step_3": "Check response to see what fields were received",
                "step_4": "View full logs here (last 50 entries)"
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@webhook_bp.route('/gumroad/debug', methods=['GET'])
def gumroad_debug():
    """View recent webhook logs for debugging"""
    try:
        logs = []
        with open('webhook_logs.jsonl', 'r') as f:
            for line in f.readlines()[-20:]:  # Last 20 entries
                logs.append(json.loads(line))
        return jsonify(logs), 200
    except FileNotFoundError:
        return jsonify({"message": "No logs yet"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# TRIAL SYSTEM ENDPOINTS
# ============================================================================

@webhook_bp.route('/trial/check-eligibility', methods=['POST'])
def trial_check_eligibility():
    """Check if user is eligible for a free trial
    
    Request body:
        {
            "email": "user@example.com",
            "hardware_id": "ABC123XYZ"
        }
    
    Response:
        {
            "eligible": true/false,
            "reason": "trial_already_used_email" | "trial_already_used_device" | null,
            "message": "..."
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email')
        hardware_id = data.get('hardware_id')
        
        if not email or not hardware_id:
            return jsonify({
                "error": "Missing required fields",
                "required": ["email", "hardware_id"]
            }), 400
        
        # Check eligibility
        result = license_manager.check_trial_eligibility(email, hardware_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Trial eligibility check failed: {e}")
        return jsonify({
            "error": "Failed to check eligibility",
            "message": str(e)
        }), 500

@webhook_bp.route('/trial/create', methods=['POST'])
def trial_create():
    """Create a new trial license
    
    Request body:
        {
            "email": "user@example.com",
            "hardware_id": "ABC123XYZ",
            "device_name": "MacBook Pro" (optional)
        }
    
    Response:
        {
            "success": true,
            "license_key": "IW-...",
            "expires": "2025-12-15T...",
            "message": "Trial license created successfully"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email')
        hardware_id = data.get('hardware_id')
        device_name = data.get('device_name', 'Unknown Device')
        
        if not email or not hardware_id:
            return jsonify({
                "error": "Missing required fields",
                "required": ["email", "hardware_id"]
            }), 400
        
        # Create trial license
        result = license_manager.create_trial_license(email, hardware_id, device_name)
        
        if result['success']:
            # Send trial-specific activation email
            try:
                email_service.send_trial_email(email, result['license_key'])
            except Exception as e:
                logger.warning(f"Failed to send trial email: {e}")
            
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Trial creation failed: {e}")
        return jsonify({
            "error": "Failed to create trial",
            "message": str(e)
        }), 500

@webhook_bp.route('/trial/status/<license_key>', methods=['GET'])
def trial_status(license_key):
    """Get trial license status
    
    Response:
        {
            "success": true,
            "is_trial": true,
            "is_active": true,
            "expires": "2025-12-15T...",
            "email": "user@example.com",
            "device_name": "MacBook Pro"
        }
    """
    try:
        licenses = license_manager.load_licenses()
        
        if license_key not in licenses:
            return jsonify({
                "error": "License not found"
            }), 404
        
        license_data = licenses[license_key]
        is_trial = license_manager.is_trial_license(license_key)
        
        return jsonify({
            "success": True,
            "is_trial": is_trial,
            "is_active": license_data.get('is_active'),
            "expires": license_data.get('expiry_date'),
            "email": license_data.get('email'),
            "device_name": license_data.get('device_name'),
            "hardware_id": license_data.get('hardware_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get trial status: {e}")
        return jsonify({
            "error": "Failed to get status",
            "message": str(e)
        }), 500

@webhook_bp.route('/license/offline-check/<license_key>', methods=['POST'])
def license_offline_check(license_key):
    """Check if a license can be used offline (for client-side grace period validation)
    
    Request body:
        {
            "email": "user@example.com",
            "hardware_id": "ABC123XYZ"
        }
    
    Response:
        {
            "can_use_offline": true/false,
            "is_trial": false,
            "days_since_last_validation": 2,
            "grace_period_remaining": 1,
            "message": "..."
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email')
        hardware_id = data.get('hardware_id')
        
        if not email or not hardware_id:
            return jsonify({
                "error": "Missing required fields",
                "required": ["email", "hardware_id"]
            }), 400
        
        licenses = license_manager.load_licenses()
        
        if license_key not in licenses:
            return jsonify({
                "error": "License not found"
            }), 404
        
        license_data = licenses[license_key]
        is_trial = license_manager.is_trial_license(license_key)
        
        # Trials NEVER work offline
        if is_trial:
            return jsonify({
                "can_use_offline": False,
                "is_trial": True,
                "message": "Trial licenses require internet connection"
            }), 200
        
        # Check grace period for paid licenses
        last_validation = license_data.get('last_validation')
        
        if not last_validation:
            return jsonify({
                "can_use_offline": False,
                "is_trial": False,
                "message": "License must be activated online first"
            }), 200
        
        last_val_date = datetime.fromisoformat(last_validation)
        days_since = (datetime.now() - last_val_date).days
        grace_remaining = max(0, 3 - days_since)
        
        can_use = days_since <= 3
        
        return jsonify({
            "can_use_offline": can_use,
            "is_trial": False,
            "days_since_last_validation": days_since,
            "grace_period_remaining": grace_remaining,
            "message": f"{'Offline use available' if can_use else 'Please connect to internet to validate'}"
        }), 200
        
    except Exception as e:
        logger.error(f"Offline check failed: {e}")
        return jsonify({
            "error": "Failed to check offline status",
            "message": str(e)
        }), 500