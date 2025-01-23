# server/utils/auth_utils.py
import os
import requests
import logging
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps
import jwt
from config import Config
load_dotenv()
SUPABASE_URL = Config.SUPABASE_URL
SUPABASE_KEY = Config.SUPABASE_KEY
SUPABASE_JWT_SECRET = Config.SUPABASE_JWT_SECRET

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT token, not Flask Sessions
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logging.debug(f"Using SECRET: {SUPABASE_JWT_SECRET[:10]}... (truncated)")
        auth_header = request.headers.get('Authorization')
        logging.debug(f"Authorization Header: {auth_header}")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Token is missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        logging.debug(f"Extracted Token: {token}")

        try:
            decoded = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            request.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"success": False, "message": f"Invalid token: {e}"}), 401

        return f(*args, **kwargs)
    return decorated
    logging.debug(f"Decoding token with SUPABASE_JWT_SECRET: {Config.SUPABASE_JWT_SECRET[:10]}...")



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Reset Password Functionality
# ---------------------------

def reset_password(reset_token: str, new_password: str) -> dict:
    """
    Update the user's password using the Supabase API.

    Args:
        reset_token (str): The reset token from the URL.
        new_password (str): The new password.

    Returns:
        dict: Success or failure message.
    """
    if not reset_token or not new_password:
        logger.error("Missing reset token or new password.")
        return {"success": False, "message": "Missing reset token or password."}

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {reset_token}",
        "Content-Type": "application/json"
    }
    payload = {"password": new_password}

    try:
        response = requests.put(f"{SUPABASE_URL}/auth/v1/user", json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Password reset successful.")
        return {"success": True, "message": "Password updated successfully."}
    except requests.RequestException as e:
        logger.error(f"Error resetting password: {e}")
        return {"success": False, "message": "Failed to reset password. Invalid or expired token."}

# Get inactive users
def get_inactive_users(inactivity_days=14):
    """
    Fetches users who have been inactive for a specified number of days.

    Args:
        inactivity_days (int): Number of days of inactivity to filter users.

    Returns:
        list: List of inactive users with their details.
    """
    try:
        cutoff_date = (datetime.utcnow() - timedelta(days=inactivity_days)).isoformat()
        response = supabase.table("users").select("id, email, last_login").lt("last_login", cutoff_date).execute()
        inactive_users = response.data if response.data else []
        return inactive_users
    except Exception as e:
        logging.error(f"Failed to fetch inactive users: {e}")
        return []
