# server/routes/debug_routes.py
from flask import Blueprint, jsonify, session, current_app
import logging

debug_bp = Blueprint('debug', __name__)

# Test Session
@debug_bp.route('/test_session')
def test_session():
    session['test_key'] = 'Session is working!'
    return jsonify({"message": "Session set successfully!"})

# Read Session
@debug_bp.route('/test_session_read')
def test_session_read():
    test_value = session.get('test_key', 'Session not found')
    return jsonify({"session_value": test_value})

# Debug Session
@debug_bp.route('/debug_session')
def debug_session():
    return jsonify(session)

# Debug Config
@debug_bp.route('/debug_config')
def debug_config():
    return {
        "SESSION_TYPE": current_app.config.get("SESSION_TYPE", "default"),
        "SESSION_FILE_DIR": current_app.config.get("SESSION_FILE_DIR", "not set")
    }
