#!/usr/bin/env python3
"""
Test license with local server (development mode)
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Force development mode
sys._called_from_test = True

# Now import the config - it should use localhost
from client.config.config import API_BASE_URL, VALIDATE_URL

print("=" * 50)
print("LICENSE CONFIGURATION TEST")
print("=" * 50)
print(f"API Base URL: {API_BASE_URL}")
print(f"Validate URL: {VALIDATE_URL}")

if "localhost" in API_BASE_URL:
    print("✅ Using LOCAL server (correct for testing)")
else:
    print("❌ Using PRODUCTION server")

# Now test the login
if __name__ == "__main__":
    # Import and run main with development mode forced
    from main import main
    main()