# API Endpoints Quick Reference

Complete API endpoint reference for ImgApp license system.

## Base URL

**Production**: `https://wavyvoy.pythonanywhere.com/api/v1`  
**Local Development**: `http://localhost:5000/api/v1`

---

## 🎯 Trial System Endpoints

### 1. Check Trial Eligibility

**Endpoint**: `POST /webhooks/trial/check-eligibility`

**Purpose**: Check if user can create a free trial

**Request**:
```json
{
  "email": "user@example.com",
  "hardware_id": "ABC123XYZ"
}
```

**Response (Eligible)**:
```json
{
  "eligible": true,
  "message": "User is eligible for a trial"
}
```

**Response (Not Eligible - Email Used)**:
```json
{
  "eligible": false,
  "reason": "trial_already_used_email",
  "message": "You have already used your free trial"
}
```

**Response (Not Eligible - Device Used)**:
```json
{
  "eligible": false,
  "reason": "trial_already_used_device",
  "message": "This device has already been used for a free trial"
}
```

---

### 2. Create Trial License

**Endpoint**: `POST /webhooks/trial/create`

**Purpose**: Create a 1-day trial license

**Request**:
```json
{
  "email": "user@example.com",
  "hardware_id": "ABC123XYZ",
  "device_name": "MacBook Pro"  // Optional
}
```

**Response (Success)**:
```json
{
  "success": true,
  "license_key": "IW-741696-ACB1830F",
  "expires": "2025-12-15T20:48:16.365558",
  "message": "Trial license created successfully"
}
```

**Response (Failed - Already Used)**:
```json
{
  "success": false,
  "error": "trial_already_used_email",
  "message": "You have already used your free trial"
}
```

---

### 3. Get Trial Status

**Endpoint**: `GET /webhooks/trial/status/<license_key>`

**Purpose**: Get current trial license status

**Response**:
```json
{
  "success": true,
  "is_trial": true,
  "is_active": true,
  "expires": "2025-12-15T20:48:16.365558",
  "email": "user@example.com",
  "device_name": "MacBook Pro",
  "hardware_id": "ABC123XYZ"
}
```

---

### 4. Check Offline Availability

**Endpoint**: `POST /webhooks/license/offline-check/<license_key>`

**Purpose**: Check if license can be used offline

**Request**:
```json
{
  "email": "user@example.com",
  "hardware_id": "ABC123XYZ"
}
```

**Response (Trial - Cannot Use Offline)**:
```json
{
  "can_use_offline": false,
  "is_trial": true,
  "message": "Trial licenses require internet connection"
}
```

**Response (Paid - Can Use Offline)**:
```json
{
  "can_use_offline": true,
  "is_trial": false,
  "days_since_last_validation": 2,
  "grace_period_remaining": 1,
  "message": "Offline use available"
}
```

**Response (Paid - Grace Expired)**:
```json
{
  "can_use_offline": false,
  "is_trial": false,
  "days_since_last_validation": 5,
  "grace_period_remaining": 0,
  "message": "Please connect to internet to validate"
}
```

---

## 💳 Gumroad Purchase Webhook

### Purchase/Refund Webhook

**Endpoint**: `POST /webhooks/gumroad`

**Purpose**: Receive purchase and refund webhooks from Gumroad

**Configure in Gumroad Dashboard**:
```
Webhook URL: https://wavyvoy.pythonanywhere.com/api/v1/webhooks/gumroad
```

**Purchase Data (from Gumroad)**:
```json
{
  "email": "customer@example.com",
  "license_key": "gumroad-key-12345",
  "sale_id": "ABC123",
  "product_id": "imgwave",
  "product_name": "ImgApp Lifetime",
  "variants[Tier]": "Lifetime",
  "price": "5",
  "currency": "usd"
}
```

**Refund Data (from Gumroad)**:
```json
{
  "email": "customer@example.com",
  "license_key": "gumroad-key-12345",
  "sale_id": "ABC123",
  "refunded": "true"  // KEY FLAG
}
```

**Response (Purchase Success)**:
```json
{
  "status": "success",
  "license_key": "IW-123456-ABCD1234",
  "email_sent": true
}
```

**Response (Refund Success)**:
```json
{
  "status": "refund_processed",
  "our_license_key": "IW-123456-ABCD1234",
  "gumroad_license_key": "gumroad-key-12345",
  "message": "License refunded and deactivated"
}
```

---

## 🔐 License Validation

### Validate License

**Endpoint**: `POST /licenses/validate`

**Purpose**: Validate license (online or offline)

**Request**:
```json
{
  "email": "user@example.com",
  "license_key": "IW-741696-ACB1830F",
  "hardware_id": "ABC123XYZ",
  "device_name": "MacBook Pro",
  "is_offline": false  // true for offline validation
}
```

**Response (Success - Trial)**:
```json
{
  "success": true,
  "message": "License validated successfully",
  "expires": "2025-12-15T20:48:16.365558",
  "is_trial": true
}
```

**Response (Success - Paid)**:
```json
{
  "success": true,
  "message": "License validated successfully",
  "expires": "2026-01-13T20:48:16.375560",
  "is_trial": false
}
```

**Response (Failed - Trial Requires Online)**:
```json
{
  "success": false,
  "error": "trial_requires_online",
  "message": "Trial licenses require internet connection for validation"
}
```

**Response (Failed - Offline Grace Expired)**:
```json
{
  "success": false,
  "error": "offline_grace_expired",
  "message": "Please connect to the internet to validate your license"
}
```

**Response (Failed - Invalid License)**:
```json
{
  "success": false,
  "error": "invalid_license"
}
```

**Response (Failed - License Deactivated)**:
```json
{
  "success": false,
  "error": "license_deactivated"
}
```

**Response (Failed - Bound to Other Device)**:
```json
{
  "success": false,
  "error": "bound_to_other_device",
  "bound_device": "MacBook Air"
}
```

---

## 🔄 License Transfer

### Transfer License to New Device

**Endpoint**: `POST /licenses/transfer`

**Purpose**: Transfer license to a new device

**Request**:
```json
{
  "email": "user@example.com",
  "license_key": "IW-741696-ACB1830F",
  "new_hardware_id": "NEW-DEVICE-456",
  "new_device_name": "Windows Desktop"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "License transferred to Windows Desktop"
}
```

---

## 📊 Diagnostic Endpoints

### View Webhook Logs

**Endpoint**: `GET /webhooks/gumroad/webhook-logs`

**Purpose**: View last 50 webhook logs for debugging

**Response**:
```json
{
  "total_logs": 50,
  "logs": [
    {
      "timestamp": "2025-12-14T20:48:16",
      "endpoint": "test-refund",
      "raw_data": {...}
    }
  ]
}
```

### View Recent Debug Logs

**Endpoint**: `GET /webhooks/gumroad/debug`

**Purpose**: View last 20 webhook debug logs

---

## 📋 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (trial license) |
| 400 | Bad Request (missing fields) |
| 404 | Not Found (invalid license) |
| 500 | Server Error |

---

## 🔑 Key Differences: Trial vs Paid

| Feature | Trial | Paid |
|---------|-------|------|
| Duration | 1 day | 30-36500 days |
| Offline Use | ❌ No | ✅ Yes (3-day grace) |
| Device Binding | Immediate | First activation |
| Abuse Prevention | Email + Device | None |
| Refundable | N/A | ✅ Yes |

---

## 🚀 Integration Examples

### Python Client

```python
import requests

# Create trial
response = requests.post(
    'https://wavyvoy.pythonanywhere.com/api/v1/webhooks/trial/create',
    json={
        'email': 'user@example.com',
        'hardware_id': get_hardware_id(),
        'device_name': get_device_name()
    }
)

if response.json()['success']:
    license_key = response.json()['license_key']
    save_license(license_key)
```

### JavaScript Client

```javascript
// Check trial eligibility
const response = await fetch(
  'https://wavyvoy.pythonanywhere.com/api/v1/webhooks/trial/check-eligibility',
  {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: 'user@example.com',
      hardware_id: getHardwareId()
    })
  }
);

const data = await response.json();
if (data.eligible) {
  // Create trial
}
```

### cURL Examples

**Create Trial**:
```bash
curl -X POST https://wavyvoy.pythonanywhere.com/api/v1/webhooks/trial/create \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","hardware_id":"ABC123","device_name":"MacBook Pro"}'
```

**Check Eligibility**:
```bash
curl -X POST https://wavyvoy.pythonanywhere.com/api/v1/webhooks/trial/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","hardware_id":"ABC123"}'
```

---

## 📞 Support

For API issues:
1. Check HTTP status code
2. Review error message in response
3. Check server/data/purchases.jsonl for audit trail
4. View webhook logs at `/webhooks/gumroad/webhook-logs`
