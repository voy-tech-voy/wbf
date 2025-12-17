#!/usr/bin/env python3
"""
Test script to verify license validation is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from client.gui.login_window import LoginWindow

# Create QApplication
app = QApplication(sys.argv)

# Create a test login window
login = LoginWindow()

print("=== Testing License Validation ===")
print()

# Test 1: Invalid credentials
print("Test 1: Invalid credentials")
print("Email: invalid@test.com")
print("License: INVALID-KEY")
result1 = login.authenticate("invalid@test.com", "INVALID-KEY")
print(f"Result: {result1}")
print()

# Test 2: Valid credentials from licenses.json
print("Test 2: Valid credentials")
print("Email: test@imgapp.com") 
print("License: IMGAPP-53BF-1F62-3E6F")
result2 = login.authenticate("test@imgapp.com", "IMGAPP-53BF-1F62-3E6F")
print(f"Result: {result2}")
print()

# Test 3: Empty credentials
print("Test 3: Empty credentials")
print("Email: ''")
print("License: ''")
result3 = login.authenticate("", "")
print(f"Result: {result3}")
print()

print("=== Validation Test Complete ===")
print(f"Invalid credentials should fail: {not result1}")
print(f"Valid credentials should pass: {result2}")
print(f"Empty credentials should fail: {not result3}")