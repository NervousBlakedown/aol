from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test fetching users
response = supabase.table("users").select("*").execute()

if response.data:
    print("Fetched users:", response.data)
else:
    print("Error fetching users or no users found:", response)
