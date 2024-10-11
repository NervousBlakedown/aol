import sqlite3
import os

# Function to initialize the database and create tables
def initialize_db():
    # Path to the SQLite database file
    db_path = 'C:\\Users\\blake\\Documents\\github\\aol\\db\\db.sqlite3'

    # Ensure the db/ folder exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Connect to the SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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

    # Seed the database with initial data (only if the users table is empty)
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("Seeding initial data...")
        cursor.executemany('''
            INSERT INTO users (username, password, email) VALUES (?, ?, ?)
        ''', [
            ('user1', 'password1', 'user1@example.com'),
            ('user2', 'password2', 'user2@example.com')
        ])

        cursor.executemany('''
            INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)
        ''', [
            (1, 2), (2, 1)
        ])

        cursor.executemany('''
            INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)
        ''', [
            (1, 2, 'Hello, how are you?'),
            (2, 1, 'I am good, thanks!')
        ])

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    initialize_db()
