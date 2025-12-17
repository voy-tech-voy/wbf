#!/usr/bin/env python3
"""
Simple test script for license upload endpoint
Use this to test if your upload endpoint is working
"""
import requests
import json

def test_upload_endpoint():
    """Test the upload endpoint with sample data"""
    
    # Sample license data for testing
    test_licenses = {
        "TEST-123-456-789": {
            "email": "test@example.com",
            "customer_name": "Test User",
            "created_date": "2025-11-18T21:00:00.000000",
            "expiry_date": "2025-12-31T23:59:59.000000",
            "is_active": True,
            "hardware_id": None,
            "device_name": None,
            "last_validation": None,
            "validation_count": 0
        }
    }
    
    try:
        print("Testing upload endpoint...")
        
        response = requests.post(
            "https://wavyvoy.pythonanywhere.com/admin/upload_licenses",
            json=test_licenses,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("Upload endpoint is working!")
                return True
            else:
                print(f"Upload failed: {result.get('error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
        
        return False
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_upload_endpoint()
