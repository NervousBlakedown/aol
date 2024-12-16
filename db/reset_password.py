from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

response = supabase.auth.admin.update_user_by_email(
    "blakecalhoun@tuta.io",
    {"password": "test123"}
)
if "error" in response:
    print(f"Error resetting password: {response['error']}")
else:
    print("Password reset successfully.")
