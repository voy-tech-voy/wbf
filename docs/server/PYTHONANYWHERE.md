# PythonAnywhere Deployment Guide for ImageWave License API

## Step 1: Create PythonAnywhere Account
1. Go to https://www.pythonanywhere.com/
2. Click "Create a Beginner account" (FREE)
3. Choose a username (remember it - you'll need it)
4. Verify your email

## Step 2: Upload Your Files
1. In PythonAnywhere dashboard, go to "Files"
2. Create a new folder called "imagewave-license-api"
3. Upload these files to that folder:
   - `production_license_api.py`
   - `wsgi.py`
   - `requirements-production.txt`

## Step 3: Install Requirements
1. Go to "Consoles" → "Bash"
2. Run these commands:
```bash
cd imagewave-license-api
pip3.10 install --user -r requirements-production.txt
```

## Step 4: Create Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select "Python 3.10"
5. Click "Next"

## Step 5: Configure Web App
1. In the "Code" section:
   - Source code: `/home/yourusername/imagewave-license-api`
   - Working directory: `/home/yourusername/imagewave-license-api`
   - WSGI configuration file: click to edit

2. Replace WSGI file content with:
```python
#!/usr/bin/python3.10

import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/imagewave-license-api'  # Change 'yourusername'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['ADMIN_PASSWORD'] = 'change-this-password'
os.environ['SECRET_KEY'] = 'change-this-secret-key'

from production_license_api import app as application
```

## Step 6: Start Your API
1. Click "Reload" button in Web tab
2. Your API will be available at: `https://yourusername.pythonanywhere.com`

## Step 7: Test Your API
Test these endpoints:
- Health check: `https://yourusername.pythonanywhere.com/health`
- API docs: `https://yourusername.pythonanywhere.com/`

## Step 8: Update ImageWave Converter
Update your `config.py` file:
```python
# Production API endpoint
PRODUCTION_LICENSE_API = "https://yourusername.pythonanywhere.com"
```

## Important Security Notes:
1. Change the ADMIN_PASSWORD in wsgi.py
2. Change the SECRET_KEY in wsgi.py
3. Keep these credentials secure!

## Free Tier Limitations:
- One web app
- Limited CPU time
- No HTTPS on custom domains (but pythonanywhere.com subdomain has HTTPS)
- Perfect for license validation API!

## Your License API Endpoints:
- Create license: `POST /api/license/create`
- Validate license: `POST /api/license/validate`  
- Transfer license: `POST /api/license/transfer`
- Admin panel: Login with your admin credentials

That's it! Your license API is now live and private on PythonAnywhere!