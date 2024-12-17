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
        "redirect_to": "https://blakeol.onrender.com/reset_password"
    }
    try:
        logging.debug("Sending password reset request to Supabase...")
        print(f"Request to Supabase: {data}")

        response = requests.post(f"{SUPABASE_URL}/auth/v1/recover", json=data, headers=headers, verify=False)
        logging.debug(f"Supabase Response Status: {response.status_code}")
        logging.debug(f"Supabase Response Body: {response.text}")
        print(f"Response Status: {response.status_code}, Response Body: {response.text}")

        response.raise_for_status() # Raise exception if status code is not 2xx
        return {"success": True, "message": "Password reset email sent successfully."}
    except requests.exceptions.RequestException as e:
        logging.error(f"Supabase API Error: {e}")
        return {"success": False, "message": str(e)}
