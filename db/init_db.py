# db/init_db.py
from dotenv import load_dotenv
import sqlite3
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from argon2 import PasswordHasher
ph = PasswordHasher()

# Explicitly specify the path to the .env file
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path=env_path)

# test URL/env correct
print("DATABASE_URL:", os.getenv('DATABASE_URL'))

def get_db_connection():
    # Fetch the database URL from environment variables
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set in environment variables.")    
    # Connect to the PostgreSQL database
    return psycopg2.connect(db_url)

def create_tables(cursor):
    # Create the 'users' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create the 'messages' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Create the 'contacts' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            contact_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (contact_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, contact_id)
        )
    ''')

def seed_data(cursor):
    # Seed initial users
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("Seeding initial data...")

        users = [
            ('user1', ph.hash('password1'), 'user1@example.com'),
            ('user2', ph.hash('password2'), 'user2@example.com')
        ]
        execute_values(cursor, '''
            INSERT INTO users (username, password, email) VALUES %s
        ''', users)

        # Seed contacts
        contacts = [
            (1, 2), (2, 1)
        ]
        execute_values(cursor, '''
            INSERT INTO contacts (user_id, contact_id) VALUES %s
        ''', contacts)

        # Seed messages
        messages = [
            (1, 2, 'Hello, how are you?'),
            (2, 1, 'I am good, thanks!')
        ]
        execute_values(cursor, '''
            INSERT INTO messages (sender_id, receiver_id, message) VALUES %s
        ''', messages)

def initialize_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        create_tables(cursor)
        seed_data(cursor)
        conn.commit()
        print("Database initialization complete.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    initialize_db()
