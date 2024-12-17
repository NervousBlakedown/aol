# server/auth_utils.py
import os
import requests
import logging
from dotenv import load_dotenv
from supabase import create_client
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Reset password functionality
def reset_password(reset_token, new_password):
    """
    Update the user's password using the Supabase API.

    Args:
        reset_token (str): The reset token from the URL.
        new_password (str): The new password.

    Returns:
        dict: Success or failure message.
    """
    if not reset_token or not new_password:
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
        return {"success": True, "message": "Password updated successfully."}
    except requests.RequestException as e:
        print(f"Error updating password: {e}")
        return {"success": False, "message": "Failed to reset password. Invalid or expired token."}