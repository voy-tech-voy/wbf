"""
API endpoint for serving centralized messages to clients
"""
from flask import jsonify, Blueprint
from server.messages import (
    SERVER_MESSAGES,
    LOGIN_MESSAGES,
    TRIAL_MESSAGES,
    FORGOT_MESSAGES,
    get_message
)

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/api/v1/messages', methods=['GET'])
def get_all_messages():
    """
    Return all messages in a structured format
    This allows clients to fetch and cache all messages on startup
    """
    try:
        all_messages = {
            "server": SERVER_MESSAGES,
            "login": LOGIN_MESSAGES,
            "trial": TRIAL_MESSAGES,
            "forgot": FORGOT_MESSAGES
        }
        
        return jsonify({
            "success": True,
            "messages": all_messages,
            "version": "1.0.0"  # Can be incremented when messages change
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@messages_bp.route('/api/v1/messages/<category>', methods=['GET'])
def get_messages_by_category(category):
    """
    Return messages for a specific category
    """
    try:
        category_map = {
            "server": SERVER_MESSAGES,
            "login": LOGIN_MESSAGES,
            "trial": TRIAL_MESSAGES,
            "forgot": FORGOT_MESSAGES
        }
        
        if category not in category_map:
            return jsonify({
                "success": False,
                "error": f"Invalid category: {category}"
            }), 400
        
        return jsonify({
            "success": True,
            "category": category,
            "messages": category_map[category]
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@messages_bp.route('/api/v1/messages/<category>/<key>', methods=['GET'])
def get_specific_message(category, key):
    """
    Return a specific message by category and key
    """
    try:
        message = get_message(category, key)
        
        if message is None:
            return jsonify({
                "success": False,
                "error": f"Message not found: {category}.{key}"
            }), 404
        
        return jsonify({
            "success": True,
            "category": category,
            "key": key,
            "message": message
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
