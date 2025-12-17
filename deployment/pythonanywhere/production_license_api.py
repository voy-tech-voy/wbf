"""
Production License Validation API Server
Optimized for deployment to cloud hosting platforms
"""

from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime, timedelta
import json
import hashlib
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Production configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    LICENSE_FILE = os.environ.get('LICENSE_FILE', 'licenses.json')
    API_KEY = os.environ.get('API_KEY')  # For admin operations

class LicenseManager:
    def __init__(self, license_file='licenses.json'):
        self.license_file = license_file
        self.ensure_license_file()
    
    def ensure_license_file(self):
        """Ensure license file exists"""
        if not os.path.exists(self.license_file):
            with open(self.license_file, 'w') as f:
                json.dump({}, f)
    
    def load_licenses(self):
        """Load licenses from file or database"""
        try:
            with open(self.license_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load licenses: {e}")
            return {}
    
    def save_licenses(self, licenses):
        """Save licenses to file or database"""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(licenses, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save licenses: {e}")
            return False
    
    def generate_license_key(self):
        """Generate a unique license key"""
        timestamp = str(int(datetime.now().timestamp()))
        random_part = secrets.token_hex(8)
        return f"IW-{timestamp[-6:]}-{random_part.upper()[:8]}"
    
    def create_license(self, email, customer_name="", expires_days=365):
        """Create a new license"""
        try:
            licenses = self.load_licenses()
            
            license_key = self.generate_license_key()
            expiry_date = datetime.now() + timedelta(days=expires_days)
            
            license_data = {
                'email': email,
                'customer_name': customer_name,
                'created_date': datetime.now().isoformat(),
                'expiry_date': expiry_date.isoformat(),
                'is_active': True,
                'hardware_id': None,
                'device_name': None,
                'last_validation': None,
                'validation_count': 0
            }
            
            licenses[license_key] = license_data
            
            if self.save_licenses(licenses):
                logger.info(f"Created license {license_key} for {email}")
                return license_key
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to create license: {e}")
            return None
    
    def validate_license(self, email, license_key, hardware_id, device_name="Unknown"):
        """Validate a license"""
        try:
            licenses = self.load_licenses()
            
            if license_key not in licenses:
                return {'success': False, 'error': 'invalid_license'}
            
            license_data = licenses[license_key]
            
            # Check if license is active
            if not license_data.get('is_active', False):
                return {'success': False, 'error': 'license_deactivated'}
            
            # Check email match
            if license_data['email'] != email:
                return {'success': False, 'error': 'email_mismatch'}
            
            # Check expiry
            expiry_date = datetime.fromisoformat(license_data['expiry_date'])
            if datetime.now() > expiry_date:
                return {'success': False, 'error': 'license_expired'}
            
            # Check hardware binding
            stored_hardware_id = license_data.get('hardware_id')
            if stored_hardware_id is None:
                # First activation - bind to this device
                license_data['hardware_id'] = hardware_id
                license_data['device_name'] = device_name
                logger.info(f"Bound license {license_key} to device {hardware_id}")
            elif stored_hardware_id != hardware_id:
                return {
                    'success': False, 
                    'error': 'bound_to_other_device',
                    'bound_device': license_data.get('device_name', 'Unknown Device')
                }
            
            # Update validation info
            license_data['last_validation'] = datetime.now().isoformat()
            license_data['validation_count'] = license_data.get('validation_count', 0) + 1
            
            licenses[license_key] = license_data
            self.save_licenses(licenses)
            
            return {
                'success': True,
                'message': 'License validated successfully',
                'expires': license_data['expiry_date']
            }
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': 'validation_failed'}
    
    def transfer_license(self, email, license_key, new_hardware_id, new_device_name="Unknown"):
        """Transfer license to a new device"""
        try:
            licenses = self.load_licenses()
            
            if license_key not in licenses:
                return {'success': False, 'error': 'invalid_license'}
            
            license_data = licenses[license_key]
            
            if license_data['email'] != email:
                return {'success': False, 'error': 'email_mismatch'}
            
            # Update device binding
            old_device = license_data.get('device_name', 'Unknown Device')
            license_data['hardware_id'] = new_hardware_id
            license_data['device_name'] = new_device_name
            license_data['last_validation'] = datetime.now().isoformat()
            
            licenses[license_key] = license_data
            self.save_licenses(licenses)
            
            logger.info(f"Transferred license {license_key} from {old_device} to {new_device_name}")
            
            return {
                'success': True,
                'message': f'License transferred to {new_device_name}'
            }
            
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            return {'success': False, 'error': 'transfer_failed'}

# Initialize license manager
license_manager = LicenseManager(Config.LICENSE_FILE)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'service': 'ImageWave License API',
        'status': 'healthy',
        'version': '1.1.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/validate', methods=['POST'])
def validate_license():
    """Validate license endpoint"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'no_data'}), 400
        
        email = data.get('email')
        license_key = data.get('license_key')
        hardware_id = data.get('hardware_id')
        device_name = data.get('device_name', 'Unknown Device')
        
        if not all([email, license_key, hardware_id]):
            return jsonify({'success': False, 'error': 'missing_parameters'}), 400
        
        result = license_manager.validate_license(email, license_key, hardware_id, device_name)
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Validation endpoint error: {e}")
        return jsonify({'success': False, 'error': 'server_error'}), 500

@app.route('/transfer', methods=['POST'])
def transfer_license():
    """Transfer license to new device endpoint"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'no_data'}), 400
        
        email = data.get('email')
        license_key = data.get('license_key')
        new_hardware_id = data.get('new_hardware_id')
        new_device_name = data.get('new_device_name', 'Unknown Device')
        
        if not all([email, license_key, new_hardware_id]):
            return jsonify({'success': False, 'error': 'missing_parameters'}), 400
        
        result = license_manager.transfer_license(email, license_key, new_hardware_id, new_device_name)
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Transfer endpoint error: {e}")
        return jsonify({'success': False, 'error': 'server_error'}), 500

@app.route('/create', methods=['POST'])
def create_license():
    """Create new license endpoint (Admin only)"""
    try:
        # Check API key for admin operations
        api_key = request.headers.get('X-API-Key')
        if Config.API_KEY and api_key != Config.API_KEY:
            return jsonify({'success': False, 'error': 'unauthorized'}), 401
        
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'no_data'}), 400
        
        email = data.get('email')
        customer_name = data.get('customer_name', '')
        expires_days = data.get('expires_days', 365)
        
        if not email:
            return jsonify({'success': False, 'error': 'email_required'}), 400
        
        license_key = license_manager.create_license(email, customer_name, expires_days)
        
        if license_key:
            return jsonify({
                'success': True,
                'license_key': license_key,
                'email': email,
                'expires_days': expires_days
            })
        else:
            return jsonify({'success': False, 'error': 'creation_failed'}), 500
        
    except Exception as e:
        logger.error(f"Create endpoint error: {e}")
        return jsonify({'success': False, 'error': 'server_error'}), 500

@app.route('/licenses', methods=['GET'])
def list_licenses():
    """List all licenses (Admin only)"""
    try:
        api_key = request.headers.get('X-API-Key')
        if Config.API_KEY and api_key != Config.API_KEY:
            return jsonify({'success': False, 'error': 'unauthorized'}), 401
        
        licenses = license_manager.load_licenses()
        
        # Remove sensitive data from response
        safe_licenses = {}
        for key, data in licenses.items():
            safe_licenses[key] = {
                'email': data.get('email'),
                'customer_name': data.get('customer_name'),
                'created_date': data.get('created_date'),
                'expiry_date': data.get('expiry_date'),
                'is_active': data.get('is_active'),
                'device_name': data.get('device_name'),
                'last_validation': data.get('last_validation'),
                'validation_count': data.get('validation_count', 0)
            }
        
        return jsonify({
            'success': True,
            'licenses': safe_licenses,
            'count': len(safe_licenses)
        })
        
    except Exception as e:
        logger.error(f"List endpoint error: {e}")
        return jsonify({'success': False, 'error': 'server_error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'endpoint_not_found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'internal_server_error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = Config.ENVIRONMENT == 'development'
    
    logger.info(f"Starting ImageWave License API Server on port {port}")
    logger.info(f"Environment: {Config.ENVIRONMENT}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)