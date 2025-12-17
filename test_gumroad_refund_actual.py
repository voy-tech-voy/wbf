#!/usr/bin/env python3
"""
Test refund handling via purchase webhook with refunded=true flag
This matches actual Gumroad behavior
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from services.license_manager import LicenseManager
from config.settings import Config

def test_gumroad_refund_flow():
    """Test the actual Gumroad refund workflow"""
    
    print("=" * 70)
    print("TEST: Gumroad Refund Flow (refunded=true flag)")
    print("=" * 70)
    
    manager = LicenseManager()
    
    # Step 1: Create initial purchase
    print(f"\n📝 Step 1: Create initial purchase")
    print(f"Simulating: Customer purchases on Gumroad")
    
    purchase_info = {
        'source': 'gumroad',
        'source_license_key': 'gumroad-key-12345-abcde',
        'sale_id': 'gumroad-sale-id-xyz',
        'customer_id': '9876543210',
        'product_id': 'product-id-123',
        'product_name': 'ImageWave Converter',
        'tier': 'Lifetime',
        'price': '500',
        'currency': 'usd',
        'purchase_date': datetime.utcnow().isoformat(),
        'is_recurring': False,
        'recurrence': None,
        'subscription_id': None,
        'is_refunded': False,
        'is_disputed': False,
        'is_test': False
    }
    
    our_license_key = manager.create_license(
        email='customer@example.com',
        customer_name='Test Customer',
        expires_days=36500,
        purchase_info=purchase_info
    )
    
    print(f"✓ License created")
    print(f"  Our key: {our_license_key}")
    print(f"  Gumroad key: {purchase_info['source_license_key']}")
    
    # Step 2: Verify license is active
    print(f"\n✅ Step 2: Verify license is active before refund")
    licenses = manager.load_licenses()
    license_data = licenses[our_license_key]
    
    assert license_data['is_active'] == True, "License should be active"
    assert license_data['source_license_key'] == 'gumroad-key-12345-abcde', "Source key should be stored"
    print(f"✓ License is active")
    print(f"  Source license key stored: {license_data['source_license_key']}")
    
    # Step 3: Simulate refund - find license by source_license_key
    print(f"\n✅ Step 3: Refund occurs on Gumroad")
    print(f"Simulating: Gumroad sends webhook with refunded=true")
    
    gumroad_refund_key = 'gumroad-key-12345-abcde'  # This is what Gumroad sends in refund webhook
    
    # Find our license by the source key
    found_key = manager.find_license_by_source_key(gumroad_refund_key)
    
    assert found_key == our_license_key, f"Should find license by source key"
    print(f"✓ Found our license by Gumroad key")
    print(f"  Gumroad key: {gumroad_refund_key}")
    print(f"  Our key: {found_key}")
    
    # Step 4: Process refund
    print(f"\n✅ Step 4: Process refund")
    refund_result = manager.handle_refund(found_key, 'gumroad_refund')
    
    assert refund_result['success'], f"Refund should succeed"
    print(f"✓ Refund processed: {refund_result['message']}")
    
    # Step 5: Verify license is deactivated
    print(f"\n✅ Step 5: Verify license is deactivated")
    licenses = manager.load_licenses()
    license_data = licenses[our_license_key]
    
    assert license_data['is_active'] == False, "License should be deactivated"
    assert license_data['refund_date'] is not None, "Refund date should be set"
    assert license_data['refund_reason'] == 'gumroad_refund', "Refund reason should be set"
    
    print(f"✓ License deactivated")
    print(f"  Is active: {license_data['is_active']}")
    print(f"  Refund date: {license_data['refund_date']}")
    print(f"  Refund reason: {license_data['refund_reason']}")
    
    # Step 6: Test validation fails
    print(f"\n✅ Step 6: Validate refunded license (should fail)")
    validation = manager.validate_license(
        email='customer@example.com',
        license_key=our_license_key,
        hardware_id='test-hardware-123'
    )
    
    assert not validation['success'], "Validation should fail for inactive license"
    assert validation['error'] == 'license_deactivated', "Error should be license_deactivated"
    
    print(f"✓ Validation correctly fails")
    print(f"  Error: {validation['error']}")
    
    # Step 7: Verify audit trail
    print(f"\n✅ Step 7: Verify refund logged to audit trail")
    refund_found = False
    with open(manager.purchases_file, 'r') as f:
        for line in f:
            record = json.loads(line)
            if record.get('license_key') == our_license_key and record.get('event') == 'refund':
                refund_found = True
                print(f"✓ Refund logged")
                print(f"  Timestamp: {record['timestamp']}")
                print(f"  Reason: {record['refund_reason']}")
                break
    
    assert refund_found, "Refund should be logged"
    
    print(f"\n" + "=" * 70)
    print(f"✅ ALL TESTS PASSED!")
    print(f"=" * 70)
    
    print(f"""
✓ Refund flow working correctly:
  1. Purchase creates license with source_license_key stored
  2. Gumroad sends webhook with refunded=true
  3. We find our license by Gumroad's license_key
  4. We deactivate it immediately
  5. Next validation fails (customer can't use app)
  6. Audit trail tracks refund

Ready for production! 🚀
    """)

if __name__ == '__main__':
    try:
        test_gumroad_refund_flow()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
