import sys
import os
import argparse
import json
from datetime import datetime, timedelta

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.license_manager import LicenseManager

def list_licenses(manager):
    licenses = manager.load_licenses()
    print(f"\n{'Email':<30} {'License Key':<25} {'Status':<10} {'Expires':<12} {'Last Validation':<20}")
    print("-" * 100)
    for key, data in licenses.items():
        status = "Active" if data.get('is_active') else "Inactive"
        expiry = data.get('expiry_date', '').split('T')[0]
        
        last_val = data.get('last_validation')
        if last_val:
            try:
                # Convert ISO format to readable date-time (YYYY-MM-DD HH:MM:SS)
                last_val = last_val.replace('T', ' ').split('.')[0]
            except:
                pass
        else:
            last_val = "Never"

        print(f"{data.get('email', 'N/A'):<30} {key:<25} {status:<10} {expiry:<12} {last_val:<20}")
    print("-" * 100)
    print(f"Total: {len(licenses)} licenses\n")

def create_license(manager, email, customer, days):
    key = manager.create_license(email, customer, days)
    if key:
        print(f"\nSUCCESS: Created license for {email}")
        print(f"Key: {key}")
        print(f"Expires in {days} days\n")
    else:
        print("\nERROR: Failed to create license\n")

def revoke_license(manager, key):
    licenses = manager.load_licenses()
    if key in licenses:
        licenses[key]['is_active'] = False
        manager.save_licenses(licenses)
        print(f"\nSUCCESS: Revoked license {key}\n")
    else:
        print(f"\nERROR: License {key} not found\n")

def main():
    parser = argparse.ArgumentParser(description="Manage ImageWave Licenses")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # List command
    subparsers.add_parser('list', help='List all licenses')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new license')
    create_parser.add_argument('--email', required=True, help='Customer email')
    create_parser.add_argument('--name', default='Customer', help='Customer name')
    create_parser.add_argument('--days', type=int, default=365, help='Validity in days')

    # Revoke command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke a license')
    revoke_parser.add_argument('key', help='License key to revoke')

    args = parser.parse_args()
    manager = LicenseManager()

    if args.command == 'list':
        list_licenses(manager)
    elif args.command == 'create':
        create_license(manager, args.email, args.name, args.days)
    elif args.command == 'revoke':
        revoke_license(manager, args.key)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
