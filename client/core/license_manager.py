"""
License Management Utilities
Handles license generation, validation, and management
"""

import uuid
import hashlib
import json
from datetime import datetime, timedelta

class LicenseManager:
    def __init__(self):
        self.licenses_file = "licenses.json"
        self.load_licenses()
    
    def load_licenses(self):
        """Load licenses from file"""
        try:
            with open(self.licenses_file, 'r') as f:
                self.licenses = json.load(f)
        except FileNotFoundError:
            self.licenses = {}
            self.save_licenses()
    
    def save_licenses(self):
        """Save licenses to file"""
        with open(self.licenses_file, 'w') as f:
            json.dump(self.licenses, f, indent=2)
    
    def generate_license_key(self):
        """Generate a new license key"""
        # Format: IMGAPP-XXXX-XXXX-XXXX
        base = str(uuid.uuid4()).upper().replace('-', '')
        return f"IMGAPP-{base[:4]}-{base[4:8]}-{base[8:12]}"
    
    def create_license(self, email, customer_name="", expires_days=365):
        """Create a new license for a customer"""
        license_key = self.generate_license_key()
        expires_date = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        license_data = {
            'email': email,
            'customer_name': customer_name,
            'license_key': license_key,
            'created': datetime.now().isoformat(),
            'expires': expires_date,
            'bound_device_id': None,
            'bound_device_name': None,
            'last_validation': None,
            'validation_count': 0,
            'active': True
        }
        
        self.licenses[license_key] = license_data
        self.save_licenses()
        
        return license_key
    
    def validate_license(self, email, license_key, hardware_id, device_name):
        """Validate a license and handle device binding"""
        if license_key not in self.licenses:
            return {'success': False, 'error': 'invalid_license'}
        
        license_data = self.licenses[license_key]
        
        # Check if license is active
        if not license_data.get('active', False):
            return {'success': False, 'error': 'license_inactive'}
        
        # Check if email matches
        if license_data['email'] != email:
            return {'success': False, 'error': 'email_mismatch'}
        
        # Check expiration
        if datetime.fromisoformat(license_data['expires']) < datetime.now():
            return {'success': False, 'error': 'license_expired'}
        
        # Handle device binding
        if license_data['bound_device_id'] is None:
            # First time activation - bind to this device
            license_data['bound_device_id'] = hardware_id
            license_data['bound_device_name'] = device_name
        elif license_data['bound_device_id'] != hardware_id:
            # License is bound to different device
            return {
                'success': False,
                'error': 'bound_to_other_device',
                'bound_device_name': license_data['bound_device_name']
            }
        
        # Update validation info
        license_data['last_validation'] = datetime.now().isoformat()
        license_data['validation_count'] += 1
        
        self.save_licenses()
        
        return {
            'success': True,
            'customer_name': license_data['customer_name'],
            'expires': license_data['expires']
        }
    
    def transfer_license(self, email, license_key, new_hardware_id, new_device_name):
        """Transfer license to a new device"""
        if license_key not in self.licenses:
            return {'success': False, 'error': 'invalid_license'}
        
        license_data = self.licenses[license_key]
        
        if license_data['email'] != email:
            return {'success': False, 'error': 'email_mismatch'}
        
        # Transfer to new device
        license_data['bound_device_id'] = new_hardware_id
        license_data['bound_device_name'] = new_device_name
        license_data['last_validation'] = datetime.now().isoformat()
        
        self.save_licenses()
        
        return {'success': True}
    
    def list_licenses(self):
        """List all licenses"""
        return self.licenses

if __name__ == "__main__":
    # Demo usage
    manager = LicenseManager()
    
    # Create a test license
    test_license = manager.create_license("test@example.com", "Test User", expires_days=30)
    print(f"Created test license: {test_license}")
    
    # Test validation
    result = manager.validate_license("test@example.com", test_license, "test-hardware-123", "Test-PC")
    print(f"Validation result: {result}")