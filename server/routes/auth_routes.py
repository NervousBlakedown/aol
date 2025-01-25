# server/routes/auth_routes.py
from flask import Blueprint, request, jsonify, session, render_template, redirect, current_app, url_for
from server.utils.auth_utils import reset_password
from server.services.user_service import create_user, authenticate_user
import logging
from supabase import create_client, Client
from werkzeug.security import check_password_hash
import os
from server.utils.db import supabase_client
import jwt
from datetime import datetime, timedelta
from urllib.parse import urlparse
from config import Config
from server.email_templates.thank_you_signup import send_thank_you_signup_email
SUPABASE_URL = Config.SUPABASE_URL
SUPABASE_KEY = Config.SUPABASE_KEY
SUPABASE_JWT_SECRET = Config.SUPABASE_JWT_SECRET
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
auth_bp = Blueprint('auth', __name__)


# extract 'aud' from supabase URL
def extract_project_id(supabase_url):
    """
    Extracts the project ID from the Supabase URL.
    Example URL: https://your-project-id.supabase.co
    """
    netloc = urlparse(supabase_url).netloc
    return netloc.split('.')[0]  # Extracts "your-project-id"


# Get username from DB
@auth_bp.route('/auth/get_username_by_id', methods=['GET'])
def get_username_by_id():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required.'}), 400

    try:
        query = '''
            SELECT 
                raw_user_meta_data->>'username' AS username
            FROM auth.users
            WHERE id = %s
        '''
        result = supabase.rpc('execute_sql', {'query': query, 'params': [user_id]})
        
        if result and len(result.data) > 0:
            username = result.data[0]['username']
            return jsonify({'success': True, 'username': username}), 200
        else:
            return jsonify({'success': False, 'message': 'Username not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching username: {str(e)}'}), 500


# Root/Signup/send 'thank you for signing up' email
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html', page_style='css/auth.css', show_video_background=True)

    # POST logic: create user in Supabase
    try:
        data = request.get_json()  # from your front-end fetch
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')

        if not email or not password or not username:
            return jsonify({"success": False, "message": "Missing email/password/username"}), 400

        # Now call Supabase sign_up
        # This creates a row in auth.users with the correct 'id' column
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username,
                    "bio": ""  # or set an initial bio if you want
                }
            }
        })

        # Check if sign-up was successful
        if response.user:
            logging.info(f"User {email} signed up successfully in Supabase.")
            return jsonify({"success": True, "message": "User signed up successfully."}), 200
        else:
            logging.warning(f"Sign-up failed in Supabase for {email}: {response}")
            return jsonify({"success": False, "message": "Sign-up failed in Supabase"}), 400

        """# Your existing user creation logic
        success = create_user(email, username, data.get('password'))
        
        if success:
            send_thank_you_signup_email(email, username)
            return jsonify({"success": True, "message": "User registered successfully."})
        else:
            return jsonify({"success": False, "message": "Registration failed."}), 400"""

    except Exception as e:
        logging.exception(f"Error signing up user: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# generate own JWT token instead of Supabase
# use 'jwt_token' as access token and 'refresh_token'; remove 'access_token' variable
def generate_access_token(user_id, email):
    secret = SUPABASE_JWT_SECRET  
    logging.debug(f"Generating token with SECRET: {SUPABASE_JWT_SECRET[:10]}...")
    project_id = extract_project_id(SUPABASE_URL)  # Dynamically fetch the project ID
    payload = {
        "sub": user_id,
        "email": email,
        # "aud": project_id,  # Supabase project reference (audience)
        "exp": datetime.utcnow() + timedelta(minutes=360),  # Expires in X hour(s)
        "iat": datetime.utcnow()  # Issued at
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token
    logging.debug(f"Using SUPABASE_JWT_SECRET from config: {Config.SUPABASE_JWT_SECRET[:10]}...")



# refresh own JWT token when needed
@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    refresh_token = data.get('refresh_token')

    if not refresh_token:
        return jsonify({"success": False, "message": "Refresh token required"}), 400

    try:
        # Validate the refresh token with Supabase
        response = supabase.auth.refresh_session({"refresh_token": refresh_token})

        if response and response.session:
            user_id = response.user.id
            email = response.user.email
            new_jwt_token = generate_access_token(user_id, email)
            return jsonify({
                "success": True,
                "jwt_token": new_jwt_token,
                "refresh_token": response.session.refresh_token
            }), 200
        else:
            return jsonify({"success": False, "message": "Invalid refresh token"}), 401

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', page_style='css/auth.css', show_video_background=True)

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Email/password required"}), 400

    try:
        # Authenticate user with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # Check if authentication was successful
        if response and response.session:
            user_id = response.user.id
            # Generate a custom JWT for the access token
            jwt_token = generate_access_token(user_id, email)
            refresh_token = response.session.refresh_token  # Keep using Supabase's refresh token

            logging.info(f"User {email} logged in successfully.")
            return jsonify({
                "success": True,
                "jwt_token": jwt_token,  # Use the custom JWT token
                "refresh_token": refresh_token,
                "redirect": "/user/dashboard"
            }), 200
        else:
            logging.error("Supabase login failed: No session or token received.")
            return jsonify({"success": False, "message": "Failed to authenticate"}), 401

    except Exception as e:
        logging.exception(f"An error occurred during login: {e}")
        return jsonify({"success": False, "message": "An error occurred during login."}), 500


# Forgot Password
@auth_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get("email")
    return reset_password(email)

# Debug secret
@auth_bp.route('/debug_secret', methods=['GET'])
def debug_secret():
    from config import Config
    return jsonify({
        "SUPABASE_JWT_SECRET": Config.SUPABASE_JWT_SECRET
    })

# Debug Supabase URL
@auth_bp.route('/debug_supabase_url', methods=['GET'])
def debug_supabase_url():
    from config import Config
    return jsonify({"SUPABASE_URL": Config.SUPABASE_URL})


# Debug Supabase key
@auth_bp.route('/debug_supabase_key', methods=['GET'])
def debug_supabase_key():
    from config import Config
    return jsonify({"SUPABASE_KEY": Config.SUPABASE_KEY})


# Debug token validation
@auth_bp.route('/debug_token_validation', methods=['POST'])
def debug_token_validation():
    from config import Config
    token = request.headers.get('Authorization').split(" ")[1]
    try:
        decoded = jwt.decode(token, Config.SUPABASE_JWT_SECRET, algorithms=["HS256"])# , audience=Config.SUPABASE_URL)
        return jsonify({"success": True, "decoded": decoded})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# Debug JWT token
@auth_bp.route('/debug_token', methods=['POST'])
def debug_token():
    from config import Config
    token = request.headers.get('Authorization').split(" ")[1]  # Extract the token
    try:
        decoded = jwt.decode(token, Config.SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return jsonify({"success": True, "decoded": decoded})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# Reset Password Page
@auth_bp.route('/reset_password', methods=['GET'])
def reset_password_page():
    reset_token = request.args.get('token')
    return render_template('auth.reset_password.html') if reset_token else "Missing reset token.", 400


# Logout
@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'success': True, 'message': 'Logged out successfully.'})
    response.delete_cookie('session')
    return response, 200