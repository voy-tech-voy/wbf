#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.config.config import API_BASE_URL, VALIDATE_URL, current_config

print(f"Current frozen state: {getattr(sys, 'frozen', False)}")
print(f"Development mode: {getattr(current_config, 'DEVELOPMENT_MODE', False)}")
print(f"API_BASE_URL: {API_BASE_URL}")
print(f"VALIDATE_URL: {VALIDATE_URL}")
print(f"Config class: {type(current_config)}")

# Test if local_config exists
try:
    import local_config
    print(f"local_config found - API_BASE_URL: {local_config.API_BASE_URL}")
except ImportError:
    print("local_config.py not found (expected for production)")

input("Press Enter to continue...")