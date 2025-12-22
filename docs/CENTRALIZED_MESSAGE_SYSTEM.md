# Centralized Message Management System

## Overview

This system allows you to update all user-facing messages from the server without requiring app updates or redeployment. Changes to messages are automatically propagated to all clients on their next startup or refresh.

## Architecture

```
┌──────────────────┐
│  Server Side     │
├──────────────────┤
│ messages.py      │  ← Define all messages here
│ api/messages.py  │  ← API endpoint to serve messages
└──────────────────┘
         ↓
    HTTP Request
         ↓
┌──────────────────┐
│  Client Side     │
├──────────────────┤
│ MessageManager   │  ← Fetches & caches messages
│ server_health.py │  ← Uses MessageManager
│ login_window.py  │  ← Uses MessageManager
└──────────────────┘
```

## Components

### 1. Server-Side (`server/messages.py`)

**Purpose**: Centralized storage of all user-facing messages

**Structure**:
```python
SERVER_HEALTH_MESSAGES = {
    "online": {
        "title": "Connected",
        "message": "Successfully connected to license server.",
        "action": None
    },
    # ... more messages
}

# Helper function
def get_message(category, key, **kwargs):
    """Get message with variable substitution"""
```

**Categories**:
- `server_health` - Connection status messages
- `login` - Login/authentication messages  
- `trial` - Trial system messages
- `forgot_license` - Password recovery messages
- `general` - Generic error/success/info/warning

### 2. API Endpoint (`server/api/messages.py`)

**Purpose**: Serve messages to clients via HTTP

**Endpoints**:
- `GET /api/v1/messages` - Get all messages
- `GET /api/v1/messages/<category>` - Get messages by category
- `GET /api/v1/messages/<category>/<key>` - Get specific message

**Response Format**:
```json
{
  "success": true,
  "messages": {
    "server_health": { ... },
    "login": { ... },
    ...
  },
  "version": "1.0.0"
}
```

### 3. Client MessageManager (`client/utils/message_manager.py`)

**Purpose**: Fetch, cache, and provide messages to client components

**Features**:
- Fetches messages from server on startup
- Caches messages locally (`message_cache.json`)
- Falls back to hardcoded messages if server unavailable
- Supports variable substitution in messages

**Usage**:
```python
from client.utils.message_manager import get_message_manager

# Initialize (done once in main.py)
msg_manager = get_message_manager(SERVER_BASE_URL)
msg_manager.fetch_from_server(timeout=3)

# Get a message
message = msg_manager.get_message(
    'server_health', 
    'offline',
    details="Connection refused"
)
# Returns: {"title": "...", "message": "...", "action": "..."}
```

### 4. Integration (`client/utils/server_health.py`)

**Purpose**: Use MessageManager in existing components

**Example**:
```python
from .message_manager import get_message_manager

msg_manager = get_message_manager()
message = msg_manager.get_message('server_health', 'offline')
```

## How to Update Messages

### Step 1: Edit Server Messages

Edit `server/messages.py`:

```python
SERVER_HEALTH_MESSAGES = {
    "offline": {
        "title": "Connection Lost",  # ← Changed title
        "message": "Unable to reach license server.\n\nACTION: Please check your internet connection.",
        "action": "Check your internet connection"
    }
}
```

### Step 2: Deploy to Server

```bash
# Commit and push to git
git add server/messages.py
git commit -m "Update offline message"
git push origin main

# Deploy to production server (PythonAnywhere, Railway, etc.)
# Messages are immediately available via /api/v1/messages endpoint
```

### Step 3: Clients Auto-Update

**On next app startup**:
1. Client fetches messages from `/api/v1/messages`
2. Caches them locally in `message_cache.json`
3. All UI components use updated messages

**No app redeployment needed!**

## Message Format

Each message has three fields:

```python
{
    "title": str,      # Short heading (e.g., "Connection Lost")
    "message": str,    # Full description with context
    "action": str|None # What user should do (can be None)
}
```

### Variable Substitution

Messages support variables using `{variable_name}`:

```python
"message": "Your license expired on {expiry_date}."
```

Usage:
```python
message = msg_manager.get_message(
    'login', 
    'license_expired',
    expiry_date="2024-12-31"
)
```

## Fallback Strategy

The system has three fallback levels:

1. **Server Messages** (Primary)
   - Fetched from `/api/v1/messages`
   - Always up-to-date

2. **Cached Messages** (Fallback 1)
   - Stored in `message_cache.json`
   - Used if server unreachable

3. **Hardcoded Messages** (Fallback 2)
   - Embedded in `message_manager.py`
   - Used if cache corrupted/missing

This ensures the app **always works**, even without internet.

## Testing

### Test Server Endpoint

```bash
# Local server
curl http://localhost:5005/api/v1/messages

# Production server
curl https://your-server.com/api/v1/messages
```

### Test Client Integration

```python
# Test MessageManager
from client.utils.message_manager import MessageManager

msg_mgr = MessageManager("http://localhost:5005")
msg_mgr.fetch_from_server()

# Get a message
msg = msg_mgr.get_message('server_health', 'offline')
print(msg)
```

### Test in Login Window

1. Run the app
2. Disconnect internet
3. Try to login
4. Should see cached/fallback messages
5. Reconnect internet
6. Restart app
7. Should fetch updated messages

## Benefits

✅ **No App Redeployment** - Update messages instantly  
✅ **Consistent Messaging** - All apps use same text  
✅ **Localization Ready** - Easy to add translations  
✅ **A/B Testing** - Change messages for different users  
✅ **Offline Support** - Works without internet (cached)  
✅ **Version Control** - Track message changes in git  

## Future Enhancements

1. **Multi-language Support**
   ```python
   GET /api/v1/messages?lang=es
   ```

2. **User-Specific Messages**
   ```python
   GET /api/v1/messages?user_id=123
   ```

3. **Message Versioning**
   ```python
   {
     "version": "1.0.0",
     "updated_at": "2024-01-15T10:30:00Z"
   }
   ```

4. **Real-Time Updates**
   - WebSocket connection
   - Push notifications for critical messages

## Maintenance

### Adding New Message Category

1. Add to `server/messages.py`:
   ```python
   PAYMENT_MESSAGES = {
       "success": {...},
       "failed": {...}
   }
   ```

2. Update API endpoint in `server/api/messages.py`:
   ```python
   category_map = {
       "payment": PAYMENT_MESSAGES
   }
   ```

3. Update client fallback in `client/utils/message_manager.py`:
   ```python
   fallback_messages = {
       "payment": {...}
   }
   ```

### Monitoring

Check message fetch success rate:
```python
# In main.py
success = msg_manager.fetch_from_server()
if not success:
    logger.warning("Using cached messages")
```

## Files Reference

| File | Purpose |
|------|---------|
| `server/messages.py` | Message definitions |
| `server/api/messages.py` | API endpoint |
| `server/app.py` | Blueprint registration |
| `client/utils/message_manager.py` | Client-side manager |
| `client/utils/server_health.py` | Integration example |
| `client/main.py` | Manager initialization |
| `message_cache.json` | Client-side cache (auto-generated) |

## Troubleshooting

### Messages Not Updating

1. **Check server endpoint**:
   ```bash
   curl http://your-server/api/v1/messages
   ```

2. **Check client cache**:
   - Delete `message_cache.json`
   - Restart app
   - Should fetch fresh messages

3. **Check logs**:
   ```python
   # Enable debug logging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Fallback Messages Used

If you see "Using cached messages" in logs:
- Server might be offline
- Network connectivity issue
- Firewall blocking requests

The app will continue working with cached/fallback messages.

## Best Practices

1. **Keep Messages Concise**
   - Title: 1-3 words
   - Message: 1-3 sentences
   - Action: Clear, actionable instruction

2. **Use Consistent Tone**
   - Professional but friendly
   - Clear and direct
   - Avoid technical jargon

3. **Test Changes**
   - Test locally before deployment
   - Verify variable substitution works
   - Check all display contexts

4. **Version Control**
   - Commit message changes with descriptive commits
   - Use semantic versioning for major changes
   - Document breaking changes

5. **Monitor Usage**
   - Track which messages are shown most
   - Gather user feedback
   - Iterate and improve
