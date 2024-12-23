# server/server.py
import requests
from flask import Flask, request, jsonify, session, redirect, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import logging
import json
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
from server.auth_utils import reset_password as reset_user_password
from supabase import create_client, Client
from cryptography.fernet import Fernet
logging.basicConfig(level=logging.DEBUG)
base_dir = os.path.abspath(os.path.dirname(__name__))
static_dir = os.path.join(base_dir, 'frontend', 'static')
template_dir = os.path.join(base_dir, 'frontend', 'templates')
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
socketio = SocketIO(app, cors_allowed_origins = "*")
app.secret_key = 'my_secret_key'  # TODO: Replace with secure, randomly generated key
app.permanent_session_lifetime = timedelta(minutes = 30)
gmail_address = os.getenv('GMAIL_ADDRESS')
gmail_password = os.getenv('GMAIL_PASSWORD')
if not gmail_address or not gmail_password:
    raise ValueError("Gmail credentials are not set in the environment variables.")
fernet_key = os.environ.get("FERNET_KEY")
f = Fernet(fernet_key.encode())

# Test signup page (better design)
@app.route('/signup_test')
def signup_test():
    return render_template('signup_test.html')

# Test .env
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

# test socket connection
@socketio.on('connect')
def handle_connect():
    logging.info(f"Client connected: {request.sid}")

# log room membership
@socketio.on('join_room')
def handle_join_room(data):
    username = data['username']
    room = data['room']
    join_room(room)
    logging.info(f"User {username} joined room {room}. SID: {request.sid}")

# Donation page
@app.route('/donate', methods = ['GET'])
def handle_donate():
    return render_template('donation.html')

# Convert ID back to Username for offline message delivery
def get_username_by_id(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT raw_user_meta_data ->> 'username' AS username
            FROM auth.users
            WHERE id = %s
        ''', (user_id,))
        user_row = cursor.fetchone()
        return user_row['username'] if user_row else None
    except Exception as e:
        logging.error(f"Error fetching username by id: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# Default page
@app.route('/', methods = ['GET'])
def default():
    return render_template('signup.html', show_video_background = True)

# Serve login page when user clicks "Already have an account? Log in"
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html', show_video_background = True)

# Signup page after clicking 'don't have account? sign up'
@app.route('/signup', methods=['GET'])
def signup_from_login():
    return render_template('signup.html', show_video_background = True)

# About page
@app.route('/about', methods = ['GET'])
def about_page():
    return render_template('about.html')

# Contact page
@app.route('/contact', methods = ['GET'])
def contact_page():
    return render_template('contact.html')

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
    return render_template('dashboard.html', show_video_background = False)

"""# dashboard test
@app.route('/dashboard_test', methods = ['GET'])
def dashboard_test():
    return render_template('dashboard_test.html')"""

# Search Contacts (exclude self from Add Pals List)
@app.route('/search_contacts', methods=['GET'])
def search_contacts():
    if 'user' not in session:
        return jsonify([]), 401  # Respond with an empty array for unauthorized users

    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify([])  # Return an empty array for empty queries

    try:
        user_id = session['user']['id']  # Get the logged-in user's ID

        # Fetch all users via Supabase Admin API
        response = supabase_admin.auth.admin.list_users()
        users = response  # Ensure response is iterable

        # Filter users based on the query and exclude the logged-in user
        matching_users = []
        for user in users:
            user_metadata = user.user_metadata
            if user_metadata and 'username' in user_metadata:
                username = user_metadata['username']
                if query in username.lower() and user.id != user_id:
                    matching_users.append({'username': username})

        return jsonify(matching_users), 200  # Return an array of matching users
    except Exception as e:
        logging.error(f"Error searching contacts: {e}")
        return jsonify([]), 500  # Always return a valid JSON array

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
        contact_user = next(
            (user for user in response if user.user_metadata.get('username') == contact_username), None
        )

        if not contact_user:
            return jsonify({'success': False, 'message': 'User not found.'}), 404

        contact_user_id = contact_user.id

        # Step 2: Check if the contact already exists
        existing_contact = supabase.table("contacts").select("id").eq("user_id", user_id).eq("contact_id", contact_user_id).execute()
        if existing_contact.data:
            return jsonify({'success': False, 'message': 'Contact already exists.'}), 409

        # Step 3: Insert contact into the 'contacts' table
        supabase.table("contacts").insert({
            "user_id": user_id,
            "contact_id": contact_user_id
        }).execute()

        return jsonify({'success': True, 'message': 'Contact added successfully.'}), 200

    except Exception as e:
        logging.error(f"Error adding contact: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while adding the contact.'}), 500

# Get contacts
@app.route('/get_my_contacts', methods=['GET'])
def get_my_contacts():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = session['user']['id']

        # Step 1: Fetch contact IDs from the 'contacts' table
        contacts_response = supabase.table("contacts") \
            .select("contact_id") \
            .eq("user_id", user_id) \
            .execute()

        contact_ids = [contact['contact_id'] for contact in contacts_response.data]

        if not contact_ids:
            return jsonify([])  # No contacts found

        # Step 2: Fetch usernames of contacts using Supabase Admin API
        response = supabase_admin.auth.admin.list_users()
        contact_users = [
            {"id": user.id, "username": user.user_metadata.get('username', 'Unknown')}
            for user in response
            if user.id in contact_ids
        ]

        return jsonify(contact_users), 200

    except Exception as e:
        logging.error(f"Error fetching contacts: {e}")
        return jsonify({'error': 'Failed to fetch contacts'}), 500

# Handle user login
@socketio.on('login')
def handle_login(data):
    username = data.get('username')
    connected_users[username] = request.sid
    user_status[username] = 'Online'

    logging.info(f"User {username} logged in. Fetching undelivered messages.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch user ID
        cursor.execute('''
            SELECT id 
            FROM auth.users 
            WHERE raw_user_meta_data ->> 'username' = %s
        ''', (username,))
        user_row = cursor.fetchone()
        if not user_row:
            logging.error(f"User not found: {username}")
            return
        user_id = user_row['id']

        # Fetch undelivered messages
        cursor.execute('''
            SELECT id, sender_id, message, room_name, timestamp 
            FROM public.messages 
            WHERE receiver_id = %s AND delivered = FALSE
        ''', (user_id,))
        undelivered_messages = cursor.fetchall()

        # Decrypt and emit messages
        for msg in undelivered_messages:
            try:
                decrypted_message = f.decrypt(msg['message'].encode()).decode()
                sender_id = msg['sender_id']
                room_name = msg['room_name']
                timestamp = msg['timestamp']

                # Emit the decrypted message to the user
                emit('message', {
                    'room': room_name,
                    'username': get_username_by_id(sender_id),
                    'message': decrypted_message,
                    'timestamp': timestamp
                }, room=request.sid)

                logging.info(f"Delivered message from {sender_id} to {username} in room {room_name}: {decrypted_message}")
            except Exception as e:
                logging.error(f"Error decrypting message ID {msg['id']}: {e}")

        # Mark all messages as delivered
        message_ids = [msg['id'] for msg in undelivered_messages]
        if message_ids:
            cursor.execute('''
                UPDATE public.messages
                SET delivered = TRUE
                WHERE id = ANY(%s)
            ''', (message_ids,))
            conn.commit()
            logging.info(f"Marked {len(message_ids)} messages as delivered for user {username}.")
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
    username = data.get('username')
    new_status = data.get('status')

    if username:
        user_status[username] = new_status  # Update the user's status
        logging.info(f"User {username} changed status to {new_status}")

        # Broadcast the updated user list to all clients
        emit('user_list', {'users': get_users_with_status()}, broadcast=True)

# Helper function to get users with their statuses
def get_users_with_status():
    users_with_status = [{'username': user, 'status': user_status.get(user, 'Offline')} for user in connected_users]
    logging.info(f"User list broadcast: {users_with_status}")
    return users_with_status

"""def get_users_with_status():
    return [{'username': user, 'status': user_status[user]} for user in connected_users]"""

# Test broadcast: serious BUG
@socketio.on('test_broadcast')
def test_broadcast():
    emit('test', {'msg': 'Broadcast test message'}, broadcast=True)
    logging.info("Broadcast test message sent.")

# Helper to generate a unique room name based on participants
def generate_room_name(users):
    return "_".join(sorted(users))  # Use sorted usernames to keep names consistent

# start chat
@socketio.on('start_chat')
def handle_start_chat(data):
    usernames = data['users']  # List of participants
    room_name = "_".join(sorted(usernames))  # Generate a consistent room name

    logging.info(f"Start chat event received for users: {usernames}, room: {room_name}")

    # Add each user to the room
    for username in usernames:
        if username in connected_users:  # Ensure the user is online
            join_room(room_name, sid=connected_users[username])
            logging.info(f"User {username} joined room {room_name}")
        else:
            logging.info(f"User {username} is not connected and cannot join room {room_name}")

    # Notify clients about the chat room
    emit('chat_started', {'room': room_name, 'users': usernames}, room=room_name)

# Join topics functionality
@socketio.on('join_topic_chat')
def join_topic_chat(data):
    room = data['room']
    username = data['username']
    join_room(room)
    emit('message', {
        'room': room,
        'username': 'System',
        'message': f'{username} has joined the {room.replace("topic_", "")} topic chat.',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }, room=room)
    print(f'{username} joined topic chat: {room}')

# Fetch all Topic messages and decrypt from encrypted DB
@app.route('/get_topic_history')
def get_topic_history():
    topic = request.args.get('topic')
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch topic messages for the specific topic (last 7 days)
        cursor.execute('''
            SELECT sender_id, message, timestamp 
            FROM public.messages 
            WHERE room_name = %s 
              AND timestamp >= NOW() - INTERVAL '7 days'
            ORDER BY timestamp ASC;
        ''', (f"topic_{topic}",))
        
        messages = cursor.fetchall()
        decrypted_messages = []

        for record in messages:
            try:
                # Ensure the message exists before attempting decryption
                encrypted_message = record['message']
                if not encrypted_message:
                    logging.warning(f"Empty message found in record: {record}")
                    decrypted_message = '[Empty Message]'
                else:
                    # Decrypt the message
                    decrypted_message = f.decrypt(encrypted_message.encode()).decode()
                    logging.info(f"Decrypted Message: {decrypted_message}")
                
                # Fetch sender username directly
                cursor.execute('''
                    SELECT raw_user_meta_data ->> 'username' AS username 
                    FROM auth.users 
                    WHERE id = %s;
                ''', (record['sender_id'],))
                
                sender_row = cursor.fetchone()
                username = sender_row['username'] if sender_row else 'Unknown'
                
                decrypted_messages.append({
                    'username': username,
                    'message': decrypted_message,
                    'timestamp': record['timestamp']
                })
            except Exception as e:
                logging.error(f"Error decrypting or processing message: {e}")
                decrypted_messages.append({
                    'username': 'System',
                    'message': '[Failed to decrypt message]',
                    'timestamp': record['timestamp']
                })

        cursor.close()
        conn.close()
        logging.info(f"Final Decrypted Messages: {decrypted_messages}")
        return jsonify({'messages': decrypted_messages}), 200

    except Exception as e:
        logging.error(f"Error fetching topic messages: {e}")
        return jsonify({'error': 'Failed to fetch messages'}), 500

# Handles Topic messages, not private
@app.route('/send_topic_message', methods=['POST'])
def send_topic_message():
    data = request.get_json()
    topic = data.get('topic')  # Topic name
    username = data.get('username')  # Sender's username
    message = data.get('message')  # Plain text message

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
    logging.info(f"Received send_topic_message event: topic={topic}, sender={username}")

    if not all([topic, username, message]):
        logging.error("Topic, username, or message is missing.")
        return jsonify({'error': 'Topic, username, and message are required'}), 400

    try:
        logging.info("🔌 Attempting to connect to the database...")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validate username in auth.users
        cursor.execute('''
            SELECT id 
            FROM auth.users 
            WHERE raw_user_meta_data ->> 'username' = %s
        ''', (username,))
        sender_row = cursor.fetchone()

        if not sender_row:
            logging.error(f"Username not found in auth.users: {username}")
            return jsonify({'error': f"Sender {username} not found."}), 404

        sender_id = sender_row['id']
        logging.info(f"Sender ID fetched: {sender_id}")

        # Encrypt the message
        encrypted_message = f.encrypt(message.encode()).decode()
        logging.info(f"Encrypted message: {encrypted_message}")

        # Insert encrypted message into public.topics
        cursor.execute('''
            INSERT INTO public.topics (name, username, message, created_at)
            VALUES (%s, 
                    (SELECT raw_user_meta_data ->> 'username' FROM auth.users WHERE raw_user_meta_data ->> 'username' = %s),
                    %s,
                    %s)
        ''', (topic, username, encrypted_message, timestamp))

        conn.commit()
        logging.info(f"Message successfully inserted into public.topics for topic: {topic}")

        # Emit the decrypted message to the topic room
        socketio.emit('topic_message', {
            'topic': topic,
            'username': username,
            'message': message,
            'timestamp': timestamp
        }, room=f"topic_{topic}", include_self=False)  # Avoid echoing back to sender

        return jsonify({'success': True, 'message': 'Message sent successfully'}), 200

    except Exception as e:
        logging.error(f"Error in send_topic_message: {e}")
        return jsonify({'error': 'Failed to send topic message'}), 500

    finally:
        cursor.close()
        conn.close()


# Send message (Private, not Topic)
@socketio.on('send_message')
def handle_send_message(data):
    room = data.get('room')
    message = data.get('message') 
    sender_username = data.get('username')
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
    logging.info(f"Received send_message event: room={room}, sender={sender_username}")

    if not message:
        logging.error("Message is missing or empty in send_message data")
        emit('error', {'msg': "Message is required."})
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch sender_id using username
        cursor.execute('''
            SELECT id 
            FROM auth.users 
            WHERE raw_user_meta_data ->> 'username' = %s
        ''', (sender_username,))
        sender_row = cursor.fetchone()
        if not sender_row:
            logging.error(f"Sender not found: {sender_username}")
            emit('error', {'msg': f"Sender {sender_username} not found."})
            return
        sender_id = sender_row['id']

        # Encrypt message
        encrypted_message = f.encrypt(message.encode()).decode()
        logging.info(f"Encrypted message: {encrypted_message}")

        # Insert encrypted message into DB
        cursor.execute('''
            INSERT INTO public.messages (sender_id, receiver_id, room_name, message, delivered, timestamp)
            VALUES ((SELECT id FROM auth.users WHERE raw_user_meta_data ->> 'username' = %s), NULL, %s, %s, FALSE, %s)
        ''', (sender_username, room, encrypted_message, timestamp))
        conn.commit()
        logging.info(f"Message successfully inserted into the database for room: {room}")

        # Emit the plain text message to the room
        emit('message', {
            'room': room,
            'username': sender_username,
            'message': message,
            'timestamp': timestamp
        }, room=room, include_self = False) # exclude sender; better than front-end logic

    except Exception as e:
        logging.error(f"Error handling send_message: {e}")
    finally:
        cursor.close()
        conn.close()

# Decrypt messages when fetching from public.messages table
def fetch_undelivered_messages(receiver_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch undelivered messages for the receiver
        cursor.execute('''
            SELECT sender_id, message, room_name, timestamp
            FROM public.messages
            WHERE receiver_id = %s AND delivered = FALSE
        ''', (receiver_id,))
        messages = cursor.fetchall()

        # Decrypt each message
        decrypted_messages = []
        for msg in messages:
            try:
                decrypted_message = f.decrypt(msg['message'].encode()).decode()
                decrypted_messages.append({
                    'sender_id': msg['sender_id'],
                    'message': decrypted_message,
                    'room': msg['room_name'],
                    'timestamp': msg['timestamp']
                })
            except Exception as e:
                logging.error(f"Error decrypting message: {e}")
        
        return decrypted_messages
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

# Remove Pal from Pals list
@app.route('/remove_contact', methods=['POST'])
def remove_contact():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    user_id = session['user']['id']
    data = request.get_json()
    contact_username = data.get('username')

    if not contact_username:
        return jsonify({'success': False, 'message': 'Contact username is required.'}), 400

    try:
        # Find the contact user by username
        response = supabase_admin.auth.admin.list_users()
        contact_user = next(
            (user for user in response if user.user_metadata.get('username') == contact_username), None
        )

        if not contact_user:
            return jsonify({'success': False, 'message': 'User not found.'}), 404

        contact_user_id = contact_user.id

        # Delete the contact from the "contacts" table
        supabase.table("contacts").delete() \
            .eq("user_id", user_id).eq("contact_id", contact_user_id) \
            .execute()

        return jsonify({'success': True, 'message': f'{contact_username} removed successfully.'}), 200

    except Exception as e:
        logging.error(f"Error removing contact: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while removing the contact.'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Logged out successfully.'}), 200

# Topics notifications route
# Subscribe to a topic
@app.route('/subscribe_topic', methods=['POST'])
def subscribe_topic():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.get_json()
    topic = data.get('topic')
    subscribe = data.get('subscribe')  # True to subscribe, False to unsubscribe
    user_id = session['user']['id']

    if not topic:
        return jsonify({'success': False, 'message': 'Topic is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if subscribe:
            cursor.execute(
                "INSERT INTO public.topic_subscriptions (user_id, topic) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (user_id, topic)
            )
        else:
            cursor.execute(
                "DELETE FROM public.topic_subscriptions WHERE user_id = %s AND topic = %s",
                (user_id, topic)
            )

        conn.commit()
        return jsonify({'success': True, 'message': f"{'Subscribed to' if subscribe else 'Unsubscribed from'} {topic}"}), 200

    except Exception as e:
        logging.error(f"Error subscribing to topic: {e}")
        return jsonify({'success': False, 'message': 'Error updating topic subscription'}), 500

    finally:
        cursor.close()
        conn.close()

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


# Reset password link
@app.route('/reset_password', methods=['GET'])
def reset_password():
    reset_token = request.args.get('token')
    if not reset_token:
        return "Missing reset token.", 400
    return render_template('reset_password.html')
    data = request.get_json()
    new_password = data.get('new_password')

    if not reset_token or not new_password:
        return jsonify({"success": False, "message": "Missing reset token or password."}), 400

    result = reset_user_password(reset_token, new_password)

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# Join topic chat logic
@socketio.on('join_topic')
def join_topic(data):
    topic_name = data.get('topic')
    username = data.get('username')

    if not topic_name or not username:
        logging.error("Topic name or username not provided")
        emit('error', {'msg': "Topic name and username are required."})
        return

    try:
        # Fetch or create the topic
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the topic exists
        cursor.execute('SELECT id FROM public.topics WHERE name = %s', (topic_name,))
        topic_row = cursor.fetchone()
        if not topic_row:
            # Create the topic if it doesn't exist
            cursor.execute('INSERT INTO public.topics (name) VALUES (%s) RETURNING id', (topic_name,))
            topic_id = cursor.fetchone()['id']
            conn.commit()
            logging.info(f"Topic created: {topic_name}")
        else:
            topic_id = topic_row['id']

        # Join the Socket.IO room for the topic
        join_room(topic_name, sid=request.sid)
        logging.info(f"User {username} joined topic: {topic_name}")

        emit('joined_topic', {'topic': topic_name, 'username': username}, room=topic_name)

    except Exception as e:
        logging.error(f"Error joining topic {topic_name}: {e}")
    finally:
        cursor.close()
        conn.close()

# Leave topic
@socketio.on('leave_topic')
def leave_topic(data):
    topic_name = data.get('topic')
    username = data.get('username')

    if not topic_name or not username:
        logging.error("Topic name or username not provided")
        emit('error', {'msg': "Topic name and username are required."})
        return

    leave_room(topic_name, sid=request.sid)
    logging.info(f"User {username} left topic: {topic_name}")
    emit('left_topic', {'topic': topic_name, 'username': username}, room=topic_name)

# Run app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)