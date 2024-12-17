# server/server.py
import requests
from flask import Flask, request, jsonify, session, redirect, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import logging
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import timedelta
from server import send_supabase_reset_email
from supabase import create_client, Client
from cryptography.fernet import Fernet
logging.basicConfig(level=logging.DEBUG)

# get paths
# print("Working Directory:", os.getcwd())
# print("Base Directory (__name__):", os.path.abspath(os.path.dirname(__name__)))
base_dir = os.path.abspath(os.path.dirname(__name__))
static_dir = os.path.join(base_dir, 'frontend', 'static')
template_dir = os.path.join(base_dir, 'frontend', 'templates')

# Load .env
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
socketio = SocketIO(app)
app.secret_key = 'my_secret_key'  # TODO: Replace with secure, randomly generated key
app.permanent_session_lifetime = timedelta(minutes = 30)

gmail_address = os.getenv('GMAIL_ADDRESS')
gmail_password = os.getenv('GMAIL_PASSWORD')
if not gmail_address or not gmail_password:
    raise ValueError("Gmail credentials are not set in the environment variables.")

# Encryption
fernet_key = os.environ.get("FERNET_KEY")
f = Fernet(fernet_key.encode())

# Test page: delete when ready
@app.route('/test', methods=['GET'])
def test():
    return render_template('index.html')

@app.route('/get_env', methods=['GET'])
def get_env():
    """
    Endpoint to provide public environment variables to the client.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'error': 'Environment variables not set'}), 500

    return jsonify({
        'SUPABASE_URL': SUPABASE_URL,
        'SUPABASE_KEY': SUPABASE_KEY
    })

# Begin
connected_users = {}
user_status = {}  # Store each user's status (Online, Away, Do Not Disturb)
rooms = defaultdict(list)

# Database connection function
def get_db_connection():
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL not set in .env")

        # Connect to Supabase
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)  # Use RealDictCursor for row-like dicts
        logging.debug("Database connection successful.")
        return conn

    except psycopg2.Error as e:
        logging.error(f"Error connecting to database: {e}")
        raise e

# Serve signup page by default (root route)
@app.route('/', methods = ['GET'])
def default():
    return render_template('signup.html')

# Serve login page when user clicks "Already have an account? Log in"
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Create account
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    if not email or not password or not username:
        return jsonify({'success': False, 'message': 'Email, password, and username are required.'}), 400

    try:
        # Properly include username in raw_user_meta_data
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username}
            }
        })

        # Check for Supabase API errors
        if response.user:
            return jsonify({'success': True, 'message': 'Signup successful!'}), 201
        else:
            return jsonify({'success': False, 'message': 'Signup failed. Try again.'}), 400
    except Exception as e:
        logging.error(f"Signup error: {e}")
        return jsonify({'success': False, 'message': 'Error during signup.'}), 500

# Login page
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required.'}), 400

    try:
        # Authenticate user with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            session['user'] = {
                'id': response.user.id,  # Save user ID for future queries
                'email': response.user.email
            }
            return jsonify({'success': True, 'message': 'Login successful.'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Error during login.'}), 500


# Get username
@app.route('/get_username', methods=['GET'])
def get_username():
    if 'user' in session:
        try:
            user_id = session['user']['id']

            # Fetch the username from raw_user_meta_data
            response = supabase_admin.auth.admin.get_user_by_id(user_id)
            if response.user:
                username = response.user.user_metadata.get('username', 'Unknown')
                return jsonify({'username': username}), 200
            else:
                return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            logging.error(f"Error fetching username: {e}")
            return jsonify({'error': 'Error retrieving username.'}), 500
    else:
        return jsonify({'error': 'Unauthorized'}), 401


# Main page
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' in session:
        try:
            user_id = session['user']['id']

            # Fetch username from raw_user_meta_data
            response = supabase_admin.auth.admin.get_user_by_id(user_id)
            username = response.user.user_metadata.get('username', 'User')

            return render_template('dashboard.html', username=username)
        except Exception as e:
            logging.error(f"Error fetching username for dashboard: {e}")
            return redirect('/login')
    else:
        return redirect('/login')

# Search Contacts
@app.route('/search_contacts', methods=['GET'])
def search_contacts():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify([])  # Return empty list if no query provided

    try:
        # Use Supabase Admin API to get all users
        response = supabase_admin.auth.admin.list_users()
        users = response # .users  # List of user objects

        # Filter users based on username in raw_user_meta_data
        matching_users = []
        for user in users:
            # user_metadata = user.get('user_metadata', {})
            user_metadata = user.user_metadata
            if user_metadata and 'username' in user_metadata:
                username = user_metadata['username']
                if query in username.lower():  # Case-insensitive search
                    matching_users.append({'username': username})

        return jsonify(matching_users), 200
    except Exception as e:
        logging.error(f"Error searching contacts: {e}")
        return jsonify({'error': 'Failed to fetch contacts'}), 500
"""def search_contacts():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('query', '')
    if not query:
        return jsonify([])  # Return empty list if no query is provided

    try:
        # Query for matching usernames in raw_user_meta_data
        response = supabase.table("auth.users").select("raw_user_meta_data").execute()
        contacts = [
            {"username": user["raw_user_meta_data"]["username"]}
            for user in response.data
            if "username" in user["raw_user_meta_data"] and query.lower() in user["raw_user_meta_data"]["username"].lower()
        ]
        return jsonify(contacts), 200
    except Exception as e:
        logging.error(f"Error searching contacts: {e}")
        return jsonify({'error': 'Failed to fetch contacts'}), 500"""


# Add contacts
@app.route('/add_contact', methods=['POST'])
def add_contact():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    user_id = session['user']['id']  # Current user's ID
    data = request.get_json()
    contact_username = data.get('username')  # Username of the contact to add

    if not contact_username:
        return jsonify({'success': False, 'message': 'Contact username is required.'}), 400

    try:
        # Step 1: Fetch all users via Supabase Admin API
        response = supabase_admin.auth.admin.list_users()

        # Step 2: Find the contact user by username
        contact_user = next(
            (user for user in response.users if user.user_metadata.get('username') == contact_username), None
        )

        if not contact_user:
            return jsonify({'success': False, 'message': 'User not found.'}), 404

        contact_user_id = contact_user.id

        # Step 3: Insert contact into the 'contacts' table
        supabase.table("contacts").insert({
            "user_id": user_id,
            "contact_id": contact_user_id
        }).execute()

        return jsonify({'success': True, 'message': 'Contact added successfully.'}), 200

    except Exception as e:
        logging.error(f"Error adding contact: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while adding the contact.'}), 500
"""def add_contact():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    user_id = session['user']['id']
    data = request.get_json()
    contact_username = data.get('username')

    if not contact_username:
        return jsonify({'success': False, 'message': 'Contact username is required.'}), 400

    try:
        # Query auth.users to find the user ID for the given username
        response = supabase.table("auth.users") \
            .select("id") \
            .filter("raw_user_meta_data->>username", "eq", contact_username) \
            .single() \
            .execute()

        contact_user_id = response.data.get('id')
        if not contact_user_id:
            return jsonify({'success': False, 'message': 'User not found.'}), 404

        # Insert into contacts table
        supabase.table("contacts").insert({
            "user_id": user_id,
            "contact_id": contact_user_id
        }).execute()

        return jsonify({'success': True, 'message': 'Contact added successfully.'}), 200
    except Exception as e:
        logging.error(f"Error adding contact: {e}")
        return jsonify({'success': False, 'message': 'Failed to add contact.'}), 500"""

# Get contacts
@app.route('/get_my_contacts', methods=['GET'])
def get_my_contacts():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = session['user']['id']

        # Query Supabase contacts table
        response = supabase.table("contacts") \
            .select("contact_id") \
            .eq("user_id", user_id) \
            .execute()

        contacts = response.data

        # Fetch usernames for these contacts
        contact_ids = [contact['contact_id'] for contact in contacts]

        users_response = supabase.table("auth.users") \
            .select("id, raw_user_meta_data") \
            .in_("id", contact_ids) \
            .execute()

        contacts_list = [
            {
                'id': user['id'],
                'username': user['raw_user_meta_data']['username']
            }
            for user in users_response.data
        ]

        return jsonify(contacts_list), 200
    except Exception as e:
        logging.error(f"Error fetching contacts: {e}")
        return jsonify({'error': 'Failed to fetch contacts'}), 500


# Handle user login via Socket.IO
@socketio.on('login')
def handle_login(data):
    username = data['username']
    connected_users[username] = request.sid
    user_status[username] = 'Online'
    emit('user_list', {'users': get_users_with_status()}, broadcast=True)
    logging.debug(f"{username} connected")

    # Fetch undelivered messages for this user
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Get all undelivered messages for this user
            # currently all messages are undelivered because we have no 'delivered' column
            # Let's assume we never delete them. 
            # In a real scenario, you might add a 'delivered' boolean column.
            # For now, just fetch all messages for receiver_id = session['user_id'] and delete after fetching
            receiver_id = session['user_id']
            cursor.execute('SELECT id, sender_id, message FROM messages WHERE receiver_id = %s', (receiver_id,))
            undelivered = cursor.fetchall()

            # Mark them as delivered by deleting
            message_ids = [row['id'] for row in undelivered]
            if message_ids:
                cursor.execute('DELETE FROM messages WHERE id = ANY(%s)', (message_ids, ))
                conn.commit()

            # Decrypt and emit these messages
            for m in undelivered:
                encrypted_msg = m['message']
                decrypted_msg = f.decrypt(encrypted_msg.encode()).decode()

                # Get sender username
                cursor.execute('SELECT username FROM users WHERE id = %s', (m['sender_id'],))
                sender_row = cursor.fetchone()
                sender_username = sender_row['username'] if sender_row else 'Unknown'

                # Determine room name
                # If this is a one-on-one chat, room name is sorted usernames
                # Let's find the current user's username and make room name
                # since we have sender_username and current username:
                room_name = "_".join(sorted([username, sender_username]))

                # Emit the message to the client
                emit('message', {'msg': decrypted_msg, 'username': sender_username, 'room': room_name}, room=request.sid)
        finally:
            cursor.close()
            conn.close()


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

# Helper to generate a unique room name based on participants
def generate_room_name(users):
    return "_".join(sorted(users))  # Use sorted usernames to keep names consistent

# Start chat
@socketio.on('start_chat')
def start_chat(data):
    usernames = data['users']
    room_name = "_".join(sorted(usernames))  # Consistent room naming based on users

    if room_name not in rooms:
        print(f"Creating new room: {room_name} for users: {', '.join(usernames)}")
        for username in usernames:
            if username in connected_users:
                join_room(room_name, sid=connected_users[username])
        rooms[room_name] = usernames  # Track participants in the room

    emit('chat_started', {'room': room_name, 'users': usernames}, room=room_name)

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    sender_email = data['username']  # Use sender's email as input
    print(f"Message received in room {room} from {sender_email}")

    if room not in rooms:
        print(f"Error: Room {room} does not exist.")
        return

    # Identify recipients (all except the sender)
    recipients = [u for u in rooms[room] if u != sender_email]

    # Emit to online recipients
    online_recipients = [r for r in recipients if r in connected_users]
    for r in online_recipients:
        emit('message', {'msg': message, 'username': sender_email, 'room': room}, room=connected_users[r])

    # Store encrypted messages for offline recipients
    offline_recipients = [r for r in recipients if r not in connected_users]
    if offline_recipients:
        encrypted_message = f.encrypt(message.encode()).decode()

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Fetch sender's ID and username from auth.users
            cursor.execute('''
                SELECT id, raw_user_meta_data 
                FROM auth.users 
                WHERE email = %s
            ''', (sender_email,))
            sender_row = cursor.fetchone()
            if not sender_row:
                print("Sender not found in auth.users")
                return
            
            sender_id = sender_row['id']
            sender_username = sender_row['raw_user_meta_data'].get('username', 'Unknown')

            # Store messages for each offline recipient
            for recipient_email in offline_recipients:
                cursor.execute('''
                    SELECT id 
                    FROM auth.users 
                    WHERE email = %s
                ''', (recipient_email,))
                recipient_row = cursor.fetchone()

                if recipient_row:
                    receiver_id = recipient_row['id']
                    cursor.execute('''
                        INSERT INTO messages (sender_id, receiver_id, message, delivered, timestamp)
                        VALUES (%s, %s, %s, %s, NOW())
                    ''', (sender_id, receiver_id, encrypted_message, False))

            conn.commit()

        except Exception as e:
            logging.error(f"Error storing offline messages: {e}")
        finally:
            cursor.close()
            conn.close()

# Typing notifications
@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    emit('typing', {'username': data['username']}, room=room, include_self=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data['room']
    emit('stop_typing', {'username': data['username']}, room=room, include_self=False)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Logged out successfully.'}), 200

# Password forget GET request
@app.route('/forgot_password', methods=['GET'])
def forgot_password_page():
    return render_template('forgot_password.html')

# Password forget POST request
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    try:
        email = request.form.get("email")
        if not email:
            return jsonify({"success": False, "message": "Please provide a valid email."}), 400
        
        logging.debug(f"Processing forgot password for email: {email}")
        result = send_supabase_reset_email(email)

        if result['success']:
            return jsonify({"success": True, "message": result['message']}), 200
        else:
            return jsonify({"success": False, "message": result['message']}), 500
    except Exception as e:
        logging.error(f"Exception in forgot_password route: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "An internal error occurred."}), 500


# Reset password (after forgotten)
@app.route('/reset_password', methods=['GET'])
def reset_password_page():
    return render_template('reset_password.html')

# Update password after 'forgot password' link
@app.route('/update_password', methods=['POST'])
def update_password():
    reset_token = request.args.get('token')  # Token passed in URL
    data = request.get_json()
    new_password = data.get("new_password")

    if not reset_token or not new_password:
        return jsonify({"success": False, "message": "Missing token or password."}), 400

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {reset_token}",
        "Content-Type": "application/json"
    }
    payload = {"password": new_password}

    try:
        response = requests.put(f"{SUPABASE_URL}/auth/v1/user", json=payload, headers=headers)
        response.raise_for_status()
        return jsonify({"success": True, "message": "Password updated successfully."}), 200
    except requests.RequestException as e:
        logging.error(f"Error updating password: {e}")
        return jsonify({"success": False, "message": "Password reset failed. Invalid token."}), 500


# Run app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)