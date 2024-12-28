# server/auth_utils.py
import os
import requests
import logging
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in your environment variables.")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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