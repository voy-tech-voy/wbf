#!/usr/bin/env python3
"""
Test the exact authentication flow that the commercial build uses
"""

import sys
import os
import json
import hashlib
import uuid
import platform
import socket
from datetime import datetime

def get_hardware_id():
    """Generate unique hardware fingerprint"""
    try:
        # Combine multiple hardware identifiers
        mac = hex(uuid.getnode())
        cpu_info = platform.processor() or 'unknown'
        system = platform.system() + platform.release()
        hostname = socket.gethostname()
        
        # Create composite fingerprint
        combined = f"{mac}-{cpu_info}-{system}-{hostname}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    except:
        # Fallback fingerprint
        return hashlib.md5(f"{platform.system()}-fallback".encode()).hexdigest()[:16]

def validate_local_file(email, license_key, hardware_id):
    """Validate license against local licenses.json file"""
    print(f"=== TESTING LOCAL FILE VALIDATION ===")
    print(f"Email: {email}")
    print(f"License Key: {license_key}")
    print(f"Hardware ID: {hardware_id}")
    
    try:
        # Check if licenses.json exists
        licenses_path = 'licenses.json'
        print(f"Looking for licenses file: {os.path.abspath(licenses_path)}")
        
        if not os.path.exists(licenses_path):
            print(f"❌ File not found: {licenses_path}")
            return False
        
        with open(licenses_path, 'r') as f:
            licenses = json.load(f)
        
        print(f"✅ Loaded {len(licenses)} licenses")
        print(f"Available license keys: {list(licenses.keys())}")
        
        if license_key not in licenses:
            print(f"❌ License key '{license_key}' not found in database")
            return False
        
        license_data = licenses[license_key]
        print(f"✅ Found license data: {license_data}")
        
        # Check if license is active
        if not license_data.get('active', False):
            print(f"❌ License is not active")
            return False
        print("✅ License is active")
        
        # Check if email matches
        if license_data['email'] != email:
            print(f"❌ Email mismatch: expected '{license_data['email']}', got '{email}'")
            return False
        print("✅ Email matches")
        
        # Check expiration
        expires_str = license_data['expires']
        expires_dt = datetime.fromisoformat(expires_str)
        now = datetime.now()
        
        if expires_dt < now:
            print(f"❌ License expired: {expires_str} < {now}")
            return False
        print(f"✅ License valid until: {expires_str}")
        
        # Handle device binding
        bound_device_id = license_data.get('bound_device_id')
        print(f"Bound device ID: {bound_device_id}")
        print(f"Current HW ID:   {hardware_id}")
        
        if bound_device_id is None:
            print("ℹ️  First time activation - would bind to this device")
            return True
        elif bound_device_id != hardware_id:
            print(f"❌ Hardware ID mismatch: bound to '{bound_device_id}', current is '{hardware_id}'")
            return False
        else:
            print("✅ Hardware ID matches bound device")
            return True
            
    except FileNotFoundError:
        print("❌ licenses.json not found")
        return False
    except Exception as e:
        print(f"❌ Local file validation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication():
    """Test the authentication with exact credentials"""
    email = "wavy.voy@gmail.com"
    license_key = "IMGAPP-1C29-53F3-80EE"
    hardware_id = get_hardware_id()
    
    print("=" * 60)
    print("TESTING COMMERCIAL BUILD AUTHENTICATION")
    print("=" * 60)
    
    result = validate_local_file(email, license_key, hardware_id)
    
    print(f"\n🔍 FINAL RESULT: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    return result

if __name__ == "__main__":
    # Change to the directory containing licenses.json
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    test_authentication()