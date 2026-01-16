import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    LICENSES_FILE = os.path.join(DATA_FOLDER, 'licenses.json')
    TRIALS_FILE = os.path.join(DATA_FOLDER, 'trials.json')

    # Email Configuration
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@imagewave.com')
    
    # Security Configuration
    # Gumroad does NOT provide webhook signatures - we verify using seller_id instead
    GUMROAD_SELLER_ID = os.environ.get('GUMROAD_SELLER_ID')  # Your Gumroad seller ID
    GUMROAD_PRODUCT_ID = os.environ.get('GUMROAD_PRODUCT_ID')  # Optional: specific product ID
    ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY')  # Set in PythonAnywhere
    
    # Enable webhook seller verification (disable in dev if needed)
    VERIFY_WEBHOOK_SELLER = os.environ.get('VERIFY_WEBHOOK_SELLER', 'true').lower() == 'true'

