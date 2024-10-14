# server.py
import eventlet
eventlet.monkey_patch() 
from argon2 import PasswordHasher
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import os
import sqlite3
logging.basicConfig(level=logging.DEBUG)
ph = PasswordHasher()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
socketio = SocketIO(app)

connected_users = {}
user_status = {}  # Store each user's status (Online, Away, Do Not Disturb)
rooms = defaultdict(list)

# Database connection function
def get_db_connection():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, '..', 'db', 'db.sqlite3')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# Serve signup page by default (root route)
@app.route('/', methods = ['GET'])
def default():
    return send_from_directory(app.static_folder, 'signup.html')


# Serve login page when user clicks "Already have an account? Log in"
@app.route('/login', methods=['GET'])
def login_page():
    return send_from_directory(app.static_folder, 'index.html')  # index.html is login page


# Signup page for POST requests (handles account creation)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    username = data['username']
    password = ph.hash(data['password']) 

    def db_task():
        conn = get_db_connection()  # Ensure absolute path
        cursor = conn.cursor()
        try:
            # Check if username or email already exists
            logging.debug(f"Checking if user {username} or email {email} exists.")
            cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                logging.warning(f"User {username} or email {email} already exists.")
                return {'success': False, 'message': 'Username or email already exists.'}

            # Insert new user into database
            logging.debug(f"Inserting user {username} into the database.")
            cursor.execute(
                'INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                (email, username, password)
            )
            conn.commit()  # Commit the transaction
            logging.info(f"User {username} successfully created.")
            return {'success': True, 'message': 'Account created successfully.'}

        except sqlite3.Error as e:  # Catch database-related errors
            logging.error(f"SQLite error: {e}")
            conn.rollback()  # Rollback on failure
            return {'success': False, 'message': f"Database error: {e}"}

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {'success': False, 'message': f"Unexpected error: {e}"}

        finally:
            cursor.close()
            conn.close()

    result = eventlet.spawn(db_task).wait()

    if result['success']:
        return jsonify(result), 201  # HTTP 201 created
    else:
        return jsonify(result), 400  # HTTP 400 bad request



# Login page
@app.route('/login', methods=['POST'])
def login():
    logging.debug("Login attempt started.")
    data = request.get_json()
    username = data['username']
    password = data['password']

    # This function performs the login-related database query
    def db_task():
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user and ph.verify(user['password'], password):
                return {'success': True, 'message': 'Login successful.'}
            else:
                return {'success': False, 'message': 'Invalid credentials.'}
        finally:
            cursor.close()
            conn.close()

    # Run the database task using eventlet's thread pool
    result = eventlet.spawn(db_task).wait()

    # Check result before returning it to the client
    if result['success']:
        return jsonify(result), 200  
    else:
        return jsonify(result), 400

# Handle user login via Socket.IO
@socketio.on('login')
def handle_login(data):
    username = data['username']
    connected_users[username] = request.sid
    user_status[username] = 'Online'  # Set status to Online by default
    emit('user_list', {'users': get_users_with_status()}, broadcast=True)
    logging.debug(f"{username} connected")


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
        logging.debug(f"{username_to_remove} disconnected.")


# Handle status change requests
@socketio.on('status_change')
def handle_status_change(data):
    username = data['username']
    new_status = data['status']
    user_status[username] = new_status  
    emit('user_list', {'users': get_users_with_status()}, broadcast=True)


# Helper function to get users with their statuses
def get_users_with_status():
    return [{'username': user, 'status': user_status[user]} for user in connected_users]

"""@app.route('/add_contact', methods=['POST'])
def add_contact():
    data = request.get_json()
    user_id = data['user_id']  # Your logged-in user ID
    contact_username = data['contact_username']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find the contact's user ID by username
        cursor.execute('SELECT id FROM users WHERE username = ?', (contact_username,))
        contact = cursor.fetchone()

        if not contact:
            return jsonify({'success': False, 'message': 'Contact not found.'}), 404

        contact_id = contact['id']

        # Insert into contacts table
        cursor.execute('INSERT OR IGNORE INTO contacts (user_id, contact_id) VALUES (?, ?)', (user_id, contact_id))
        conn.commit()

        return jsonify({'success': True, 'message': 'Contact added successfully.'})
    except Exception as e:
        logging.error(f"Error adding contact: {e}")
        return jsonify({'success': False, 'message': 'Error adding contact.'}), 500
    finally:
        conn.close()"""

# Start a one-on-one or group chat
@socketio.on('start_chat')
def start_chat(data):
    usernames = data['users']
    room_name = '_'.join(sorted(usernames))  # Create unique room name based on users
    print(f"Starting chat in room: {room_name} with users: {', '.join(usernames)}")

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
    print(f"Message sent from {username} in room {room}.")
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
