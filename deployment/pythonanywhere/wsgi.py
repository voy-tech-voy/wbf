#!/usr/bin/python3.10

"""
WSGI config for PythonAnywhere deployment
"""

import sys
import os

# Add your project directory to the Python path
path = '/home/wavyvoy/imagewave-license-api'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables for production
os.environ['FLASK_ENV'] = 'production'
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['ADMIN_PASSWORD'] = 'your-secure-admin-password-here'
os.environ['SECRET_KEY'] = 'your-secret-key-here-change-this'

# Email Configuration
os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
os.environ['SMTP_PORT'] = '587'
os.environ['SMTP_USERNAME'] = 'methos014@gmail.com'  # Your Gmail account
os.environ['SMTP_PASSWORD'] = 'your-gmail-app-password-here'  # Use Gmail App Password, not regular password
os.environ['FROM_EMAIL'] = 'methos014@gmail.com'  # Email to show in "From" field

if __name__ == "__main__":
    application.run()