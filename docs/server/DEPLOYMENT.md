# ImageWave Converter v1.1.0 - Production Deployment Guide

## License Validation System Overview

### Architecture
```
[ImageWave App] --> [Production API Server] --> [License Database]
       |                                              |
       └-- [Offline Validation] --------> [Local License Cache]
```

## Production Requirements

### 1. **Production API Server Setup**

You need to deploy the license validation server to a production environment:

#### Option A: Cloud Hosting (Recommended)
- **AWS Lambda + API Gateway** (serverless)
- **Heroku** (easy deployment)
- **DigitalOcean App Platform**
- **Azure Functions**
- **Google Cloud Functions**

#### Option B: VPS/Dedicated Server
- **Ubuntu/CentOS server**
- **Docker containerization**
- **HTTPS with SSL certificate**

### 2. **Domain & API Endpoint**
Replace `https://api.imagewave.dev` in `config.py` with your actual domain:

```python
# In config.py - Update this line:
API_BASE_URL = "https://your-domain.com"  # Your actual API domain
```

### 3. **Database Setup**
The current system uses local JSON files. For production, you need:

#### Recommended: PostgreSQL/MySQL Database
```sql
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    hardware_id VARCHAR(255),
    device_name VARCHAR(255),
    last_validation TIMESTAMP,
    validation_count INTEGER DEFAULT 0
);
```

#### Alternative: Cloud Database
- **AWS RDS** (PostgreSQL/MySQL)
- **Google Cloud SQL**
- **Azure Database**
- **MongoDB Atlas**

### 4. **Security Considerations**

#### API Security
- **HTTPS only** (SSL certificate required)
- **API key authentication** for server-to-server
- **Rate limiting** to prevent abuse
- **CORS configuration** for web interfaces

#### License Security
- **Encrypted license keys** (current system uses this)
- **Hardware fingerprinting** (already implemented)
- **Expiration validation** (implemented)
- **Device binding** (implemented)

### 5. **Production Deployment Steps**

#### Step 1: Prepare Production API Server
```bash
# 1. Deploy license_api_server.py to your hosting platform
# 2. Update database connection (replace JSON with real DB)
# 3. Configure environment variables:
export DATABASE_URL="postgresql://user:pass@host:port/db"
export API_SECRET_KEY="your-secret-key"
export ALLOWED_DOMAINS="*.imagewave.dev"
```

#### Step 2: Update Application Configuration
```bash
# Update config.py with production API URL
# Build production executable
.\imgapp_venv\Scripts\pyinstaller.exe --onefile --windowed --name="ImageWave-Converter-v1.1.0" main.py
```

#### Step 3: Test Production Validation
1. Deploy API server
2. Create test license through API
3. Build production executable
4. Test license validation flow
5. Test offline validation fallback

### 6. **License Generation Process**

#### For Customer Sales:
```python
# Create license via API:
POST https://your-domain.com/create
{
    "email": "customer@email.com",
    "customer_name": "Customer Name",
    "expires_days": 365
}
```

#### Customer Receives:
1. **Email address**: Their login email
2. **License key**: Generated unique key
3. **Download link**: To ImageWave Converter installer
4. **Instructions**: How to activate

#### First-Time Activation:
1. Customer downloads and installs ImageWave Converter
2. Runs application → Login window appears
3. Enters email + license key
4. Application validates online → binds to hardware
5. Stores local validation for offline use

### 7. **Monitoring & Analytics**

#### Track License Usage:
- Validation attempts
- Active devices
- License transfers
- Expiration warnings

#### Implement Logging:
```python
# Add to your production API
import logging
logging.info(f"License validated: {email} on {device_name}")
```

## Current Development vs Production

### ✅ **Already Implemented (Ready for Production)**
- Hardware fingerprinting
- License encryption and validation
- Offline validation fallback
- Device binding and transfer
- Development mode bypass
- Professional UI with branding

### 🚧 **Still Needed for Production**
1. **Production API hosting** (deploy license_api_server.py)
2. **Real database** (replace JSON files)
3. **Production domain** (update config.py)
4. **SSL certificate** (HTTPS required)
5. **Customer license generation interface**

### 📋 **Recommended Next Steps**
1. Choose hosting platform (AWS/Heroku/DigitalOcean)
2. Set up production database
3. Deploy API server
4. Update config.py with production URLs
5. Create customer license generation interface
6. Build and test production executable

## Example Production URLs

Once deployed, your license validation will work like this:

```
Development: http://localhost:5001/validate
Production:  https://api.imagewave.dev/validate
```

The app automatically detects development vs production mode and uses the appropriate endpoint.