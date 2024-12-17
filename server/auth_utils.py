# server/auth_utils.py
import os
import requests
import logging
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Send reset email for forgotten password
def send_supabase_reset_email(email):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "redirect_to": "https://blakeol.onrender.com/reset_password"
    }
    try:
        logging.debug("Attempting to send password reset request to Supabase.")
        # Safely print request for debugging
        logging.debug(f"Request Payload: {data}")

        # Send request to Supabase
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/recover", 
            json=data, 
            headers=headers, 
            timeout=10,  # Prevent hanging requests
            verify=False  # Only for debugging SSL issues (remove in production)
        )

        # Log status and body
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response Text: {response.text}")

        # Raise error for non-2xx responses
        response.raise_for_status()
        return {"success": True, "message": "Password reset email sent successfully."}

    except requests.exceptions.RequestException as e:
        # Log only once, avoid recursion
        logging.error(f"Supabase request failed: {e}", exc_info=False)
        return {"success": False, "message": "Failed to send password reset email. Please try again later."}

    except Exception as e:
        # Catch any unexpected errors safely
        logging.error(f"Unexpected error in send_supabase_reset_email: {e}", exc_info=False)
        return {"success": False, "message": "An unexpected error occurred."}

