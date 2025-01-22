# server/__init__.py
from flask import Flask, redirect, request
from flask_socketio import SocketIO
from config import Config
import os
from dotenv import load_dotenv
import logging
from datetime import timedelta
load_dotenv()

# Initialize Flask app
app = Flask(
    __name__,
    static_folder=os.path.join(os.getcwd(), 'frontend', 'static'),
    static_url_path='/static',
    template_folder=os.path.join(os.getcwd(), 'frontend', 'templates')
)

# Use Config class for Flask app configuration
app.config.from_object(Config)

# Supabase credentials injection
@app.context_processor
def inject_supabase_creds():
    return {
        'SUPABASE_URL': Config.SUPABASE_URL,
        'SUPABASE_KEY': Config.SUPABASE_KEY
    }


# Prevent Connection Timeouts
app.config['ENV'] = 'development'
app.config['DEBUG'] = Config.DEBUG
app.config['USE_RELOADER'] = False

# Root Route - Redirect to Signup
@app.route('/', methods=['GET'])
def root():
    return redirect('/auth/signup')

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins='*')

# Logging Configuration
logging.basicConfig(level=logging.DEBUG if Config.DEBUG else logging.INFO)

# Validate Gmail credentials
if not Config.GMAIL_ADDRESS or not Config.GMAIL_PASSWORD:
    raise ValueError("Gmail credentials are not set in environment variables.")

# Import Blueprints
from .routes.auth_routes import auth_bp
from .routes.user_routes import user_bp
from .routes.chat_routes import chat_bp
from .routes.misc_routes import misc_bp
from .routes.debug_routes import debug_bp
from .routes.notifications_routes import notifications_bp
from .routes.news_routes import news_bp

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(misc_bp)  # Global
app.register_blueprint(debug_bp, url_prefix='/debug')
app.register_blueprint(notifications_bp, url_prefix='/notifications')
app.register_blueprint(news_bp)

# Debug Sessions (Optional, for development)
@app.before_request
def debug_request():
    logging.debug(f"Request Headers: {dict(request.headers)}")
    logging.debug(f"Request Path: {request.path}")

# Socket.IO Events
from .socketio_events import *