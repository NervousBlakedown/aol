import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
from supabase import create_client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

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
        DATABASE_URL = self._load_env('DATABASE_URL')

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


# Singleton Instance
supabase_client = SupabaseClient()