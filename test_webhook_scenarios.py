#!/usr/bin/env python3
"""
Webhook Testing Utility
Test different Gumroad webhook scenarios to understand exact data format

Run this to test what your endpoints receive
"""

import requests
import json
from datetime import datetime

# Your PythonAnywhere URL
BASE_URL = "https://wavyvoy.pythonanywhere.com"

# Test scenarios
SCENARIOS = {
    "scenario_1_refund_event": {
        "description": "Gumroad sends separate refund event",
        "endpoint": "/api/v1/webhooks/gumroad/test-refund",
        "data": {
            "resource_type": "sale",
            "action": "refunded",
            "id": "YhDQXVee5s7VpKkO_W0lLQ==",
            "license_key": "5E7C7E2C-54D04A60-A428A513-BB73D489",
            "refund_reason": "customer_request",
            "timestamp": datetime.utcnow().isoformat()
        }
    },
    
    "scenario_2_refund_flag": {
        "description": "Refund flag in purchase webhook",
        "endpoint": "/api/v1/webhooks/gumroad/test-refund",
        "data": {
            "id": "YhDQXVee5s7VpKkO_W0lLQ==",
            "email": "customer@example.com",
            "license_key": "5E7C7E2C-54D04A60-A428A513-BB73D489",
            "product_name": "ImageWave Converter",
            "price": "500",
            "refunded": "true",
            "refund_timestamp": datetime.utcnow().isoformat()
        }
    },
    
    "scenario_3_transaction_ids": {
        "description": "Using transaction_id instead of license_key",
        "endpoint": "/api/v1/webhooks/gumroad/test-refund",
        "data": {
            "transaction_id": "YhDQXVee5s7VpKkO_W0lLQ==",
            "gumroad_license_key": "5E7C7E2C-54D04A60-A428A513-BB73D489",
            "customer_email": "customer@example.com",
            "product_name": "ImageWave Converter",
            "refunded": "true",
            "refund_date": datetime.utcnow().isoformat()
        }
    },
    
    "scenario_4_minimal": {
        "description": "Minimal refund data",
        "endpoint": "/api/v1/webhooks/gumroad/test-refund",
        "data": {
            "sale_id": "YhDQXVee5s7VpKkO_W0lLQ==",
            "license_key": "5E7C7E2C-54D04A60-A428A513-BB73D489",
            "refunded": "true"
        }
    }
}


def test_webhook(scenario_name, scenario_data):
    """Send test webhook and show response"""
    
    endpoint = scenario_data["endpoint"]
    url = BASE_URL + endpoint
    data = scenario_data["data"]
    
    print(f"\n{'='*70}")
    print(f"Testing: {scenario_name}")
    print(f"Description: {scenario_data['description']}")
    print(f"{'='*70}")
    
    print(f"\n📤 Sending to: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, data=data, timeout=10)
        
        print(f"\n✓ Response Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Connection failed - Is PythonAnywhere running?")
        print(f"  Check: {url}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def get_webhook_logs():
    """Retrieve and display webhook logs"""
    
    url = f"{BASE_URL}/api/v1/webhooks/gumroad/webhook-logs"
    
    print(f"\n{'='*70}")
    print(f"📋 Retrieving Webhook Logs")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✓ Total logs: {data.get('total_logs', 0)}")
            
            if data.get('logs'):
                print(f"\nLatest logs:")
                for i, log in enumerate(data['logs'][-5:], 1):  # Last 5
                    print(f"\n  [{i}] Timestamp: {log.get('timestamp')}")
                    print(f"      Endpoint: {log.get('endpoint')}")
                    print(f"      Received fields: {list(log.get('raw_data', {}).keys())}")
            else:
                print(f"\nNo logs yet - try sending a test webhook first")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"\n✗ Error fetching logs: {e}")


def main():
    """Main testing menu"""
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════╗
║                 GUMROAD WEBHOOK TESTING UTILITY                        ║
║                                                                         ║
║  This tool tests what Gumroad actually sends in refund webhooks       ║
║  by sending test data to your webhook endpoints                        ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"\nTesting against: {BASE_URL}")
    print(f"\nAvailable scenarios:")
    for i, (name, scenario) in enumerate(SCENARIOS.items(), 1):
        print(f"  {i}. {name}: {scenario['description']}")
    
    print(f"\nOptions:")
    print(f"  (1-4)  Test specific scenario")
    print(f"  (a)    Test all scenarios")
    print(f"  (l)    Get webhook logs")
    print(f"  (q)    Quit")
    
    while True:
        choice = input(f"\nEnter choice: ").strip().lower()
        
        if choice == 'q':
            print(f"Exiting...")
            break
        
        elif choice == 'l':
            get_webhook_logs()
        
        elif choice == 'a':
            for name, scenario in SCENARIOS.items():
                test_webhook(name, scenario)
                input(f"\nPress Enter to continue...")
        
        elif choice in ['1', '2', '3', '4']:
            idx = int(choice) - 1
            scenario_name, scenario_data = list(SCENARIOS.items())[idx]
            test_webhook(scenario_name, scenario_data)
        
        else:
            print(f"Invalid choice. Try again.")


if __name__ == '__main__':
    main()
