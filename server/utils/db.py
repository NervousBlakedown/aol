# server/utils/db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
import logging
from config import Config
import supabase
supabase_client = supabase.create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
logger = logging.getLogger(__name__)


# Supabase creds class
class SupabaseClient:
    def __init__(self):
        self.supabase = None

    def _load_env(self, key):
        """
        Load environment variables, prioritizing `current_app.config` if available.
        """
        return current_app.config.get(key) or os.getenv(key)

    def initialize_client(self):
        """
        Initialize the Supabase client using service role key.
        """
        SUPABASE_URL = self._load_env('SUPABASE_URL')
        SUPABASE_SERVICE_ROLE_KEY = self._load_env('SUPABASE_SERVICE_ROLE_KEY')

        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError('Supabase configuration (URL or Service Role Key) is missing.')

        try:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            logging.info('✅ Supabase client initialized successfully.')
        except Exception as e:
            logging.error(f"❌ Failed to initialize Supabase client: {e}")
            raise e

    def get_supabase_client(self):
        """
        Get the Supabase client instance.
        """
        if not self.supabase:
            self.initialize_client()
        return self.supabase

    def get_db_connection(self):
        """
        Always return a new PostgreSQL database connection.
        """
        DATABASE_URL = os.getenv('DATABASE_URL')

        if not DATABASE_URL:
            raise ValueError("DATABASE_URL not set in app.config or .env")

        try:
            conn = psycopg2.connect(
                DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            logging.info('✅ New PostgreSQL database connection established successfully.')
            return conn
        except psycopg2.Error as e:
            logging.error(f"❌ Error connecting to PostgreSQL: {e}")
            raise e


# fetch new users for automated 'thank you for signing up' emails n'at
def fetch_new_users():
    """
    Fetches new users from the Supabase auth.users table who signed up today.
    This function should be scheduled to run a few times a day.
    """
    sql_query = """
        SELECT id, email, raw_user_meta_data->>'username' AS username, created_at
        FROM auth.users
        WHERE created_at >= CURRENT_DATE
        AND welcome_email_sent = FALSE;
    """

    try:
        db_client = supabase_client.get_db_connection()
        with db_client.cursor() as cursor:
            cursor.execute(sql_query)
            users = cursor.fetchall()
            db_client.close()
            return users
    except Exception as e:
        logger.error(f"❌ Error fetching new users: {e}")
        return []


# mark email as sent (no duplicates for new users, please)
def mark_email_as_sent(user_id):
    """
    Marks the welcome email as sent in the database.
    """
    sql_query = """
        UPDATE auth.users
        SET welcome_email_sent = TRUE
        WHERE id = %s;
    """

    try:
        db_client = supabase_client.get_db_connection()
        with db_client.cursor() as cursor:
            cursor.execute(sql_query, (user_id,))
            db_client.commit()
            db_client.close()
            logger.info(f"✅ Welcome email marked as sent for user ID {user_id}")
    except Exception as e:
        logger.error(f"❌ Error updating email sent status: {e}")


# Singleton Instance
supabase_client = SupabaseClient()