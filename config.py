# config.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL', 'not in config')
    SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD', 'not in config')
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'not in config')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'not in config')
    GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS', 'not in config')
    GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', 'not in config')
    FERNET_KEY = os.getenv('FERNET_KEY', 'not in config')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'not in config')
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret_key')
    SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', 60)) * 60  # Default 60 minutes
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', 'not in config')

    @classmethod
    def validate(cls):
        """Ensure all required environment variables are set."""
        required_keys = [
            "DATABASE_URL", "SUPABASE_URL", "SUPABASE_KEY",
            "SUPABASE_SERVICE_ROLE_KEY", "FERNET_KEY"
        ]
        for key in required_keys:
            if getattr(cls, key) == 'not in config':
                raise ValueError(f"Missing required environment variable: {key}")