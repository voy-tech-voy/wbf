#!/usr/bin/env python3

import sys
import os

# Add the path where config might be
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from client.config.config import API_BASE_URL, VALIDATE_URL
    print(f"API_BASE_URL: {API_BASE_URL}")
    print(f"VALIDATE_URL: {VALIDATE_URL}")
    
    try:
        import local_config
        print(f"local_config found: {local_config.API_BASE_URL}")
    except ImportError:
        print("local_config.py not found")
        
except Exception as e:
    print(f"Error importing config: {e}")

input("Press Enter to continue...")