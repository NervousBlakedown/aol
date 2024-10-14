import sqlite3
import os
from argon2 import PasswordHasher

ph = PasswordHasher()

def get_db_connection(db_path):
    # Ensure the db/ folder exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # Connect to the SQLite database (it will be created if it doesn't exist)
    return sqlite3.connect(db_path)

def create_tables(cursor):
    # Create the 'users' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create the 'messages' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    ''')

    # Create the 'contacts' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            contact_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (contact_id) REFERENCES users(id),
            UNIQUE(user_id, contact_id)
        )
    ''')

def seed_data(cursor):
    # Check if the users table is empty and seed data if it is
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("Seeding initial data...")
        users = [
            ('user1', ph.hash('password1'), 'user1@example.com'),
            ('user2', ph.hash('password2'), 'user2@example.com')
        ]
        cursor.executemany('''
            INSERT INTO users (username, password, email) VALUES (?, ?, ?)
        ''', users)

        contacts = [
            (1, 2), (2, 1)
        ]
        cursor.executemany('''
            INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)
        ''', contacts)

        messages = [
            (1, 2, 'Hello, how are you?'),
            (2, 1, 'I am good, thanks!')
        ]
        cursor.executemany('''
            INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)
        ''', messages)

def initialize_db():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'db.sqlite3')
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        create_tables(cursor)
        seed_data(cursor)
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    initialize_db()
