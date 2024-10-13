# server.py
import eventlet
eventlet.monkey_patch() # must go first

from argon2 import PasswordHasher
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import os
import sqlite3
import threading

logging.basicConfig(level=logging.DEBUG)
ph = PasswordHasher()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
socketio = SocketIO(app)

connected_users = {}
user_status = {}  # Store each user's status (Online, Away, Do Not Disturb)
rooms = defaultdict(list)

# Database connection function
def get_db_connection():
    try:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, '../db/db.sqlite3')
        conn = sqlite3.connect(db_path, check_same_thread = False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        print(f"Error connecting to database: {e}")
        raise

# Serve signup page by default
@app.route('/', methods = ['GET'])
def default():
    return send_from_directory(app.static_folder, 'signup.html')
"""@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')"""

"""# Signup route for GET requests (serves the signup page)
@app.route('/signup', methods=['GET'])
def signup_page():
    return send_from_directory(app.static_folder, 'signup.html')"""

# Signup page for POST requests (handles account creation)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    username = data['username']
    password = data['password']

    # Hash the password
    hashed_password = ph.hash(password)

    # This function performs the database operations
    def db_task():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the username or email already exists
            cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                return {'success': False, 'message': 'Username or email already exists.'}

            # Insert the new user into the database
            cursor.execute(
                'INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                (email, username, hashed_password),
            )
            conn.commit()
            return {'success': True}
        except Exception as e:
            logging.error(f"Database error: {e}")
            return {'success': False, 'message': 'Error occurred while creating account.'}
        finally:
            conn.close()

    # Run the database task using eventlet's tpool (thread pool)
    result = eventlet.tpool.execute(db_task)

    # check result before returning it to client
    if result['success']:
        return jsonify(result), 201 # HTTP 201 created
    else:
        return jsonify(result)
    
"""def signup():
    data = request.get_json()
    email = data['email']
    username = data['username']
    password = data['password']

    hashed_password = ph.hash(password)

    def db_task():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            return {'success': False, 'message': 'Username or email already exists.'}
        
        try:
            cursor.execute(
                'INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                (email, username, hashed_password),
            )
            conn.commit()
        except Exception as e:
            print(f"Database error: {e}")
            return {'success': False, 'message': 'Error occurred while creating account.'}
        finally:
            conn.close()
        
        return {'success': True}

    # Run the database task in a separate thread
    result = threading.Thread(target=db_task).start()
    return jsonify(result)"""

"""@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    username = data['username']
    password = data['password']
    hashed_password = ph.hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        return jsonify({'success': False, 'message': 'Username or email already exists.'})

    try:
        cursor.execute(
            'INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
            (email, username, hashed_password),
        )
        conn.commit()
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'message': 'Error occurred while creating account.'})
    finally:
        conn.close()

    return jsonify({'success': True})"""


# Login page
@app.route('/login', methods=['POST'])
def login():
    logging.debug("Login attempt started.")
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user and ph.verify(user['password'], password): #bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({'success': True, 'message': 'Login successful.'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials.'})
    except Exception as e:
        print("Error during login:", e)
        return jsonify({'success': False, 'message': 'An error occurred during login.'})
    finally:
        conn.close()

# Handle user login via Socket.IO
@socketio.on('login')
def handle_login(data):
    username = data['username']
    connected_users[username] = request.sid
    user_status[username] = 'Online'  # Set status to Online by default
    emit('user_list', {'users': get_users_with_status()}, broadcast=True)
    print(f"{username} connected")

# WebSocket handler for disconnecting users
@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    username_to_remove = None
    for username, sid_value in connected_users.items():
        if sid_value == sid:
            username_to_remove = username
            break
    if username_to_remove:
        del connected_users[username_to_remove]
        del user_status[username_to_remove]
        emit('user_list', {'users': get_users_with_status()}, broadcast=True)
        print(f"{username_to_remove} disconnected")

# Handle status change requests
@socketio.on('status_change')
def handle_status_change(data):
    username = data['username']
    new_status = data['status']
    user_status[username] = new_status  # Update the user's status
    emit('user_list', {'users': get_users_with_status()}, broadcast=True)

# Helper function to get users with their statuses
def get_users_with_status():
    return [{'username': user, 'status': user_status[user]} for user in connected_users]

# Start a one-on-one or group chat
@socketio.on('start_chat')
def start_chat(data):
    usernames = data['users']
    room_name = '_'.join(sorted(usernames))  # Create unique room name based on users
    for username in usernames:
        if username in connected_users:
            join_room(room_name, sid=connected_users[username])
    rooms[room_name].extend(usernames)
    emit('chat_started', {'room': room_name, 'users': usernames}, room=room_name)

# Handle sending messages
@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    username = data['username']
    emit('message', {'msg': message, 'username': username}, room=room, include_self = False)

# Typing notifications
@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    emit('typing', {'username': data['username']}, room=room, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data['room']
    emit('stop_typing', {'username': data['username']}, room=room, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
