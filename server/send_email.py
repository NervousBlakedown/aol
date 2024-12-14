import os
import requests
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")

def send_email(user_email):
    # Define the email payload
    email_payload = {
        "to": user_email,
        "subject": "Welcome to BlakeOL",
        "html": "<strong>Thank you for creating a BlakeOL account!</strong>",
        "text": "Thank you for creating a BlakeOL account!"
    }

    # Send the email using Supabase REST API
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/send_email",
            headers={
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            json=email_payload,
        )
        if response.status_code == 200:
            print("Email sent successfully!")
        else:
            print(f"Error sending email: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending email: {e}")
