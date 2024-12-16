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

def migrate_users():
    # Fetch existing users from your custom "users" table
    response = supabase.table("users").select("*").execute()

    # Check if there was an error or if no users were found
    if response.error:
        print("Error fetching users:", response.error)
        return

    users = response.data
    if not users:
        print("No users found in the 'users' table.")
        return

    print(f"Fetched {len(users)} users for migration.")

    for user in users:
        try:
            # Migrate each user to `auth.users`
            result = supabase.auth.admin.create_user(
                {
                    "email": user["email"],
                    "password": "temporary_password",  # Temporary password for migration
                    "email_confirm": True,  # Mark email as verified
                    "user_metadata": {"username": user["username"]},
                }
            )

            if result.error:
                print(f"Error migrating user {user['email']}: {result.error.message}")
                continue

            print(f"User {user['email']} migrated successfully.")

        except Exception as e:
            print(f"Exception migrating user {user['email']}: {e}")

if __name__ == "__main__":
    migrate_users()
    

