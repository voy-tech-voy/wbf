#!/usr/bin/env python3
"""
Test script to see what configuration the commercial build would use
"""

import sys
import os
import json

# Simulate the commercial build environment
def simulate_commercial_environment():
    print("=" * 60)
    print("TESTING COMMERCIAL BUILD CONFIGURATION")
    print("=" * 60)
    
    # Check if we're in a bundled environment (like the commercial build)
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        bundle_dir = sys._MEIPASS
        print(f"✅ Running in bundled mode")
        print(f"Bundle directory: {bundle_dir}")
    else:
        # Running in normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"⚠️  Running in development mode")
        print(f"Script directory: {bundle_dir}")
    
    # Check for local_config.json
    local_config_path = os.path.join(bundle_dir, 'local_config.json')
    print(f"\nLooking for local_config.json at: {local_config_path}")
    
    if os.path.exists(local_config_path):
        print("✅ local_config.json found!")
        with open(local_config_path, 'r') as f:
            local_config = json.load(f)
        print(f"Config content: {local_config}")
        api_base_url = local_config.get('api_base_url', 'NOT FOUND')
    else:
        print("❌ local_config.json NOT found!")
        api_base_url = "https://wavyvoy.pythonanywhere.com"  # Default production
    
    print(f"\nAPI Base URL would be: {api_base_url}")
    
    # Test what config.py would actually do
    print("\n" + "=" * 40)
    print("TESTING CONFIG.PY BEHAVIOR")
    print("=" * 40)
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import client.config.config as config
        print(f"Config API Base URL: {config.API_BASE_URL}")
        print(f"Development Mode: {config.DEVELOPMENT_MODE}")
    except Exception as e:
        print(f"Error importing config: {e}")

if __name__ == "__main__":
    simulate_commercial_environment()