#!/usr/bin/env python3
"""
Test production server license validation
"""

import requests
import json

def test_production_server():
    """Test the production license validation server"""
    
    # Production server URL
    base_url = "https://wavyvoy.pythonanywhere.com"
    validate_url = f"{base_url}/validate"
    
    print("=" * 60)
    print("TESTING PRODUCTION SERVER")
    print("=" * 60)
    print(f"Server: {base_url}")
    print(f"Validate URL: {validate_url}")
    
    # Test data
    test_data = {
        'email': 'wavy.voy@gmail.com',
        'license_key': 'IMGAPP-1C29-53F3-80EE',
        'hardware_id': 'edf58327a9b5ca53',
        'device_name': 'Windows-DESKTOP-1LGKSK7',
        'app_version': '1.1.0'
    }
    
    print(f"\nTesting with license: {test_data['license_key']}")
    print(f"Email: {test_data['email']}")
    
    try:
        print("\n🔄 Sending validation request...")
        response = requests.post(validate_url, json=test_data, timeout=15)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Production server validation successful!")
                return True
            else:
                print(f"❌ Production server validation failed: {result.get('error', 'Unknown error')}")
                return False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - server may be slow or unreachable")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server may be down")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_production_server()
    
    if success:
        print("\n🎉 Production server is ready for commercial build testing!")
    else:
        print("\n⚠️  Production server issues detected. Check server logs.")
    
    print("\nNext step: Test ImgApp_Commercial.exe with your license credentials")