from flask import Flask
from config.settings import Config
from api import api_bp, webhook_bp
from api.messages import messages_bp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(webhook_bp, url_prefix='/api/v1/webhooks')
    app.register_blueprint(messages_bp)  # Messages endpoint at /api/v1/messages

    @app.route('/', methods=['GET'])
    def health_check():
        return {"status": "online", "service": "ImageWave License API"}

    return app

if __name__ == '__main__':
    app = create_app()
    import os
    port = int(os.environ.get('PORT', 5005))
    # Bind to 0.0.0.0 to ensure it listens on all interfaces
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)