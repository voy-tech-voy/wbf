#!/usr/bin/env python3
"""
Test different license validation scenarios
"""

import requests
import json

def test_license_scenarios():
    """Test various license scenarios"""
    
    # Test scenarios
    scenarios = [
        {
            "name": "Current License (Local)",
            "email": "wavy.voy@gmail.com",
            "license_key": "IMGAPP-1C29-53F3-80EE"
        },
        {
            "name": "Test License",
            "email": "test@imgapp.com", 
            "license_key": "IMGAPP-53BF-1F62-3E6F"
        },
        {
            "name": "Production Test",
            "email": "test@example.com",
            "license_key": "TEST-1234-5678-9012"
        }
    ]
    
    base_url = "https://wavyvoy.pythonanywhere.com"
    validate_url = f"{base_url}/validate"
    
    print("=" * 70)
    print("TESTING PRODUCTION LICENSE SCENARIOS")
    print("=" * 70)
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}")
        print(f"   Email: {scenario['email']}")
        print(f"   License: {scenario['license_key']}")
        
        test_data = {
            'email': scenario['email'],
            'license_key': scenario['license_key'],
            'hardware_id': 'test-hardware-123',
            'device_name': 'Test-Device',
            'app_version': '1.1.0'
        }
        
        try:
            response = requests.post(validate_url, json=test_data, timeout=10)
            result = response.json()
            
            if result.get('success'):
                print(f"   ✅ SUCCESS: {result}")
            else:
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
    
    print(f"\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    print("1. 🔄 Set up licenses on production server")
    print("2. 🧪 Test with ImgApp_Commercial.exe") 
    print("3. 🔧 Or use ImgApp_Commercial_Local.exe for local testing")

if __name__ == "__main__":
    test_license_scenarios()