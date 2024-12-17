import os
import requests
import logging
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def send_supabase_reset_email(email):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "redirect_to": "https://blakeol.onrender.com/forgot_password"
    }
    try:
        response = requests.post(f"{SUPABASE_URL}/auth/v1/recover", json=data, headers=headers)
        response.raise_for_status()
        return {"success": True, "message": "Password reset email sent successfully."}
    except requests.exceptions.RequestException as e:
        logging.error(f"Supabase API Error: {e}")
        return {"success": False, "message": str(e)}
