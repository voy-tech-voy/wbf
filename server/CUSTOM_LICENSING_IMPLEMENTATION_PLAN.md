# Custom Licensing & Server Implementation Plan

## 1. System Overview
We are building a custom licensing server hosted on **PythonAnywhere** to manage trial access, license validation, and payment integration for ImgApp.

### Core Requirements
1.  **Trial System**: 10 free conversions per machine (Hardware ID locked).
2.  **Licensing**: 
    - Supports One-time and Subscription payments.
    - Hardware-locked (1 machine per license).
    - **Reset Policy**: User can switch machines (reset Hardware ID) once every 7 days.
3.  **Automation**: 
    - Payment (Gumroad/Stripe) -> Webhook -> Server generates/updates license -> Email sent to user.

---

## 2. Architecture

### A. Folder Structure
We will organize the server code to separate concerns (API, Data, Logic).

```text
server/
├── api/
│   ├── __init__.py
│   ├── routes.py           # API endpoints (validate, activate, trial)
│   └── webhooks.py         # Payment processor webhooks (Gumroad)
├── config/
│   ├── __init__.py
│   └── settings.py         # Secrets, paths, email config
├── data/
│   ├── licenses.json       # Main license database (or SQLite)
│   └── trials.json         # Track trial usage by Hardware ID
├── services/
│   ├── __init__.py
│   ├── license_manager.py  # Logic for creating/validating licenses
│   ├── trial_manager.py    # Logic for trial counting
│   └── email_service.py    # Logic for sending emails (SMTP/SendGrid)
├── templates/
│   └── email_license.html  # Email template for new licenses
├── app.py                  # Entry point
└── wsgi.py                 # PythonAnywhere hook
```

### B. Data Models

#### 1. License Model (`licenses.json`)
```json
{
  "LICENSE-KEY-123": {
    "email": "user@example.com",
    "type": "lifetime",       // or "subscription"
    "status": "active",       // active, suspended, expired
    "hardware_id": "HWID-ABC",
    "created_at": "2025-12-12T10:00:00",
    "expires_at": null,       // or date for subscription
    "last_reset_date": "2025-12-01T10:00:00", // For 7-day reset rule
    "validation_count": 5
  }
}
```

#### 2. Trial Model (`trials.json`)
```json
{
  "HWID-ABC": {
    "conversions_used": 3,
    "first_seen": "2025-12-12T10:00:00",
    "last_seen": "2025-12-12T11:00:00"
  }
}
```

---

## 3. Functional Logic

### A. Trial Logic (The "10 Free Files" Rule)
*   **Client-Side**: 
    *   Check local encrypted counter.
    *   If < 10, allow conversion.
    *   Increment counter.
    *   **Sync**: Periodically (or on startup) check with server `/api/trial/status` sending HWID.
*   **Server-Side**:
    *   Endpoint: `POST /api/trial/record`
    *   Payload: `{ "hardware_id": "..." }`
    *   Logic: 
        *   If HWID exists, increment count. 
        *   If count >= 10, return `{"allowed": false}`.
    *   *Security*: Prevents user from just deleting local config to reset trial.

### B. License Validation & Hardware Binding
*   **Validation**:
    *   Client sends: `Key` + `Hardware ID`.
    *   Server checks:
        1.  Key exists?
        2.  Key not expired?
        3.  **Hardware ID matches?**
            *   If `None` (new license): Bind current HWID.
            *   If Match: Success.
            *   If Mismatch: Fail (License in use on another machine).

### C. Machine ID Reset Policy (The "7-Day" Rule)
*   **Scenario**: User buys new PC or reinstalls OS.
*   **Action**: User requests "Reset License" via Client UI.
*   **Server Logic**:
    *   Check `last_reset_date`.
    *   If `None` OR `(Now - last_reset_date) > 7 days`:
        *   Clear `hardware_id`.
        *   Update `last_reset_date` = Now.
        *   Return Success.
    *   Else:
        *   Return Error: "You can only switch machines once every 7 days. Next reset available on [Date]."

### D. Payment & Email Flow
1.  **User** buys on Gumroad.
2.  **Gumroad** sends Webhook (`POST`) to `https://imgapp.pythonanywhere.com/api/webhooks/gumroad`.
3.  **Server**:
    *   Verifies webhook signature.
    *   Extracts email and product info.
    *   Generates unique License Key (e.g., `IMG-XXXX-XXXX`).
    *   Saves to `licenses.json`.
    *   Calls `EmailService` to send Key to User.

---

## 4. API Endpoints Draft

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/v1/trial/check` | Check if HWID has remaining trial conversions. |
| `POST` | `/api/v1/trial/increment` | Record a conversion for HWID. |
| `POST` | `/api/v1/license/validate` | Validate Key + HWID. Returns Token if valid. |
| `POST` | `/api/v1/license/reset` | Request to unbind HWID (subject to 7-day rule). |
| `POST` | `/api/v1/webhooks/gumroad` | Receive payment notification. |

---

## 5. Implementation Roadmap

### Phase 1: Server Structure & Trial API
*   [ ] Set up folder structure.
*   [ ] Implement `TrialManager` and `trials.json`.
*   [ ] Create `/api/v1/trial/*` endpoints.
*   [ ] Update Client to use Trial API.

### Phase 2: License Management Core
*   [ ] Implement `LicenseManager` and `licenses.json`.
*   [ ] Create `/api/v1/license/validate` endpoint.
*   [ ] Implement Hardware ID binding logic.
*   [ ] Implement 7-day reset logic.

### Phase 3: Payment & Automation
*   [ ] Create Webhook endpoint for Gumroad.
*   [ ] Implement Key Generation logic.
*   [ ] Implement `EmailService` (SMTP or API).

### Phase 4: Client Integration
*   [ ] Update Client "Login/License" window.
*   [ ] Add "Reset License" button/flow.
*   [ ] Add "Trial: X/10 remaining" indicator.

---

## 6. Alternative Solutions Considered
*   **Keygen.sh / Cryptolens**: Dedicated licensing APIs. 
    *   *Pros*: Less code to maintain, robust features.
    *   *Cons*: Monthly cost, external dependency.
*   **Gumroad License API**: 
    *   *Pros*: Built-in.
    *   *Cons*: Limited control over "7-day reset" logic and specific HWID binding rules.
*   **Decision**: **Custom PythonAnywhere Solution**.
    *   *Reason*: We already have the server, zero extra cost, full control over the specific "10 files" and "7-day reset" logic.
