"""
Centralized Message Definitions for ImgApp
All user-facing messages defined here for easy updates across all clients
"""

# Version of message definitions (increment when messages change)
MESSAGE_VERSION = "1.0.0"

# Server Health Messages
SERVER_MESSAGES = {
    'online': {
        'title': '✅ Connected',
        'message': 'Server is online and responsive.',
        'action': None
    },
    'slow': {
        'title': '⚠️ Slow Connection',
        'message': 'Your request may take longer than usual.\n\nPlease be patient.',
        'action': 'Continue anyway'
    },
    'maintenance': {
        'title': '🔧 Maintenance Mode',
        'message': 'The server is currently under maintenance.\n\nThis usually takes only a few minutes.',
        'action': 'Retry in 5 minutes'
    },
    'overloaded': {
        'title': '🚦 Server Busy',
        'message': 'The server is handling many requests right now.\n\nPlease wait a moment and try again.',
        'action': 'Retry in 30 seconds'
    },
    'offline': {
        'title': '❌ Server Offline',
        'message': 'Cannot connect to the license server.\n\n'
                  'Possible reasons:\n'
                  '• Server maintenance\n'
                  '• Your internet connection is down\n'
                  '• Temporary server overload\n'
                  '• Firewall blocking connection',
        'action': 'Check internet connection and try again'
    },
    'timeout': {
        'title': '⏱️ Connection Timeout',
        'message': 'The server is not responding.\n\n'
                  'This may be temporary. Please check:\n'
                  '• Your internet connection\n'
                  '• Firewall settings',
        'action': 'Try again in a moment'
    },
    'circuit_open': {
        'title': '🔌 Connection Failed',
        'message': 'The app has stopped trying to connect after multiple failures.\n\n'
                  'This protects both your computer and the server.',
        'action': 'Wait and try again'
    },
    'unknown': {
        'title': '⚠️ Unknown Error',
        'message': 'An unexpected error occurred.',
        'action': 'Please contact support if this persists'
    }
}

# Trial Messages
TRIAL_MESSAGES = {
    'trial_already_used_email': {
        'title': 'Trial Already Used',
        'message': 'You have used your free trial with this email address.',
        'action': None
    },
    'trial_already_used_hardware': {
        'title': 'Trial Already Used',
        'message': 'This device has been used for a free trial.',
        'action': None
    },
    'trial_not_eligible': {
        'title': 'Not Eligible',
        'message': 'You are not eligible for a trial at this time.',
        'action': None
    },
    'trial_success': {
        'title': 'Trial Activated',
        'message': 'Your trial license has been activated successfully!',
        'action': 'Continue'
    },
    'trial_no_internet': {
        'title': 'No Internet Connection',
        'message': 'An internet connection is required to activate a trial.\n\nPlease check your connection and try again.',
        'action': None
    }
}

# Login Messages
LOGIN_MESSAGES = {
    'login_success': {
        'title': 'Login Successful',
        'message': 'Welcome back!',
        'action': None
    },
    'login_invalid': {
        'title': 'Invalid Credentials',
        'message': 'The email or license key you entered is incorrect.',
        'action': 'Please try again'
    },
    'license_expired': {
        'title': 'License Expired',
        'message': 'Your license has expired. Please renew to continue.',
        'action': 'Visit store to renew'
    },
    'email_mismatch': {
        'title': 'Email Mismatch',
        'message': 'This license key is registered to a different email address.',
        'action': 'Check your email'
    }
}

# Forgot License Messages
FORGOT_MESSAGES = {
    'forgot_success': {
        'title': 'Email Sent',
        'message': 'Your license key has been sent to your email address.',
        'action': None
    },
    'forgot_not_found': {
        'title': 'No License Found',
        'message': 'No license was found for this email address.',
        'action': 'Check your email or contact support'
    },
    'forgot_rate_limit': {
        'title': 'Too Many Requests',
        'message': 'Please wait a few minutes before trying again.',
        'action': 'Try again later'
    }
}

# Combine all messages
ALL_MESSAGES = {
    'server': SERVER_MESSAGES,
    'trial': TRIAL_MESSAGES,
    'login': LOGIN_MESSAGES,
    'forgot': FORGOT_MESSAGES,
    'version': MESSAGE_VERSION
}


def get_message(category: str, key: str, **kwargs) -> dict:
    """
    Get a message by category and key with optional formatting
    
    Args:
        category: 'server', 'trial', 'login', or 'forgot'
        key: Message key within the category
        **kwargs: Optional values to format the message
    
    Returns:
        dict with 'title', 'message', 'action' keys
    """
    messages = ALL_MESSAGES.get(category, {})
    message = messages.get(key, {
        'title': 'Error',
        'message': 'An unknown error occurred.',
        'action': None
    })
    
    # Format message if kwargs provided
    if kwargs:
        message = message.copy()
        message['message'] = message['message'].format(**kwargs)
    
    return message
