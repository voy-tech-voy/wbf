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

from server.app import app as application

if __name__ == "__main__":
    application.run()