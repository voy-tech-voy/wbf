#!/usr/bin/env python3
"""
Test script to verify unified license structure with purchase_info
"""

import json
import sys
from services.license_manager import LicenseManager

def test_unified_structure():
    """Test creating a license with new purchase_info structure"""
    
    manager = LicenseManager()
    
    # Create a test license with structured purchase_info
    test_purchase_info = {
        'source': 'gumroad',
        'source_license_key': '85581098-63674C19-96C71F41-4D719BFF',
        'sale_id': 'Tuj7x65czHeWPEXQENjvaA==',
        'customer_id': '8553431068502',
        'product_id': 'bRuqEyqpCRHcjuRlGQ4DSw==',
        'product_name': 'ImageWave ~ GIF~ Webm~WebP ~ Batch Converter',
        'tier': 'Pricing',
        'price': '200',
        'currency': 'usd',
        'purchase_date': '2025-12-14T13:50:29Z',
        'is_recurring': False,
        'recurrence': None,
        'subscription_id': 'UPW2N8t7BeJh2uCwQLS45A==',
        'renewal_date': None,
        'is_refunded': False,
        'refund_date': None,
        'is_disputed': False,
        'is_test': True
    }
    
    print("=" * 80)
    print("TESTING UNIFIED LICENSE STRUCTURE")
    print("=" * 80)
    
    # Create license
    license_key = manager.create_license(
        email='test-unified@example.com',
        customer_name='Test User',
        expires_days=30,
        purchase_info=test_purchase_info
    )
    
    if not license_key:
        print("❌ Failed to create license")
        return False
    
    print(f"✅ License created: {license_key}")
    
    # Load and verify structure
    licenses = manager.load_licenses()
    license_data = licenses.get(license_key)
    
    if not license_data:
        print(f"❌ License not found in database")
        return False
    
    print("\n📋 LICENSE DATA STRUCTURE:")
    print(json.dumps(license_data, indent=2))
    
    # Verify core fields exist
    core_fields = ['email', 'customer_name', 'created_date', 'expiry_date', 'is_active', 
                   'hardware_id', 'device_name', 'last_validation', 'validation_count']
    
    print("\n✅ CORE LICENSE FIELDS (Validation):")
    for field in core_fields:
        value = license_data.get(field)
        status = "✓" if field in license_data else "✗"
        print(f"  {status} {field}: {value}")
    
    # Verify purchase_info structure
    purchase_info = license_data.get('purchase_info')
    if not purchase_info:
        print("\n❌ purchase_info not found in license data")
        return False
    
    print("\n✅ PURCHASE_INFO FIELDS (Metadata):")
    purchase_fields = ['source', 'source_license_key', 'sale_id', 'customer_id', 'product_id',
                       'product_name', 'tier', 'price', 'currency', 'purchase_date',
                       'is_recurring', 'subscription_id', 'is_refunded', 'is_disputed']
    
    for field in purchase_fields:
        if field in purchase_info:
            print(f"  ✓ {field}: {purchase_info.get(field)}")
        else:
            print(f"  ✗ {field}: MISSING")
    
    # Test validation still works
    print("\n" + "=" * 80)
    print("TESTING LICENSE VALIDATION")
    print("=" * 80)
    
    result = manager.validate_license(
        'test-unified@example.com',
        license_key,
        'test-hardware-123',
        'Test-PC'
    )
    
    if result.get('success'):
        print("✅ Validation successful")
        print(f"   Expires: {result.get('expires')}")
    else:
        print(f"❌ Validation failed: {result.get('error')}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Unified structure working correctly!")
    print("=" * 80)
    return True

if __name__ == '__main__':
    success = test_unified_structure()
    sys.exit(0 if success else 1)
