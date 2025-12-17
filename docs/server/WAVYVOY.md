# 🚀 wavyvoy's PythonAnywhere Deployment Guide

## Your API URL: https://wavyvoy.pythonanywhere.com

### Step 1: Upload Files ✅ READY
1. Go to your PythonAnywhere dashboard
2. Click on "Files" tab
3. Create new folder: `imagewave-license-api`
4. Upload these 4 files from your `pythonanywhere_deploy` folder:
   - `production_license_api.py` (12.7KB)
   - `wsgi.py` (624B)
   - `requirements-production.txt` (259B)
   - `README.txt` (296B)

### Step 2: Install Requirements
1. Click "Consoles" → "Bash"
2. Run these commands exactly:
```bash
cd imagewave-license-api
pip3.10 install --user -r requirements-production.txt
```

### Step 3: Create Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select "Python 3.10"
5. Click "Next"

### Step 4: Configure Web App
In the "Code" section, set:
- **Source code**: `/home/wavyvoy/imagewave-license-api`
- **Working directory**: `/home/wavyvoy/imagewave-license-api`

### Step 5: WSGI Configuration
1. Click on the WSGI configuration file link
2. **Replace ALL content** with this:

```python
#!/usr/bin/python3.10

import sys
import os

# Add your project directory to the Python path
path = '/home/wavyvoy/imagewave-license-api'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['ADMIN_PASSWORD'] = 'ImageWave2024!'  # Change this!
os.environ['SECRET_KEY'] = 'wavyvoy-secret-key-change-this'  # Change this!

from production_license_api import app as application
```

### Step 6: Launch Your API! 🎯
1. Click the green "Reload" button
2. Your API is now live at: **https://wavyvoy.pythonanywhere.com**

### Step 7: Test Your API
- Health check: https://wavyvoy.pythonanywhere.com/health
- API documentation: https://wavyvoy.pythonanywhere.com/

### Step 8: Update Your ImageWave App ✅ ALREADY DONE!
Your `config.py` is already updated to use: `https://wavyvoy.pythonanywhere.com`

### 🔐 IMPORTANT Security Notes:
1. **Change the passwords** in the WSGI file above
2. **Keep your admin credentials secure**
3. **Don't share these credentials publicly**

### 🎉 What You'll Have:
- **Private license API** at https://wavyvoy.pythonanywhere.com
- **Admin panel** for creating/managing licenses
- **Full commercial licensing system**
- **100% free forever**

Once deployed, your ImageWave Converter will automatically connect to your private API server!