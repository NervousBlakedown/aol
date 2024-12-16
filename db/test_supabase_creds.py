from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Check if environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

email = "blakecalhoun@tuta.io"  # Replace with your test user's email
password = "$kol_Yinz_Fide$311" # Replace with your test user's password

# Test login
try:
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if 'error' in response:
        print(f"Login failed: {response['error']['message']}")
    else:
        print("Login successful:", response)
except Exception as e:
    print("Error during login:", e)