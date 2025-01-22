# server/services/chat_service.py
from flask import jsonify, current_app
from flask_socketio import emit, join_room
from server.utils.db import supabase_client
from server.utils.encryption import f
from datetime import datetime, timezone
import logging
from server import socketio

#########################
# DATABASE
#########################
def search_users_by_username(search_query):
    """
    Search for users in the auth.users table by their username.
    Returns a list of matching usernames.
    """
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        
        # Use ILIKE for case-insensitive search
        cursor.execute('''
            SELECT raw_user_meta_data->>'username' AS username
            FROM auth.users
            WHERE raw_user_meta_data->>'username' ILIKE %s
            LIMIT 10
        ''', (f'%{search_query}%',))
        
        rows = cursor.fetchall()
        users = [{"username": row["username"]} for row in rows]

        return jsonify({"success": True, "users": users}), 200

    except Exception as e:
        logging.error(f"Error searching users: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to search users"}), 500

    finally:
        cursor.close()
        conn.close()


#########################
#  PRIVATE CHATS
#########################
def start_chat(users):
    """
    users = ["blake_test", "luke3d.ai", "blake_again"] ...
    Build underscore-based room_name => e.g. "blake_again_blake_test_luke3d.ai"
    Return a Flask Response tuple: (jsonify({ success, room }), status_code)
    """
    if not users:
        return jsonify({"success": False, "message": "No users provided"}), 400

    sorted_users = sorted(users)
    room_name = "_".join(sorted_users)
    current_app.logger.info(f"✅ Created/Found chat room: {room_name}")

    # If you needed to store the chat in your DB, do it here.
    # For example: insert a row in `chats` table, or verify chat doesn't exist, etc.

    # Return JSON with success + the newly created room name
    return jsonify({"success": True, "room": room_name}), 200


# Fetch chat history (decrypted in the front, party (encrypted) in the back )
def fetch_chat_history(room):
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                auth.users.raw_user_meta_data->>'username' AS sender_username,
                public.messages.message,
                public.messages.timestamp
            FROM public.messages
            JOIN auth.users ON public.messages.sender_id = auth.users.id
            WHERE public.messages.room_name = %s
            ORDER BY public.messages.timestamp ASC
        ''', (room,))
        rows = cursor.fetchall()

        messages = []
        for row in rows:
            encrypted_msg = row["message"]  # The stored cipher text

            try:
                decrypted_msg = f.decrypt(encrypted_msg.encode()).decode()
            except Exception as e:
                logging.error(f"Decryption failed for message: {encrypted_msg}. Error: {e}")
                decrypted_msg = "[Decryption failed]"

            messages.append({
                "username": row["sender_username"],
                "message": decrypted_msg,
                "timestamp": row["timestamp"]
            })

        return jsonify({"success": True, "messages": messages}), 200

    except Exception as e:
        logging.error(f"Error fetching chat history: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch chat history"}), 500
    finally:
        cursor.close()
        conn.close()


# Handle private messages "Chats" section
def handle_private_message(data):
    """
    For storing a private message in DB + emitting real-time to the room.
    data = {
      "room": "...",
      "username": "...",
      "message": "..."
    }
    """
    current_app.logger.debug(f"Received data for handle_private_message: {data}")
    room = data.get('room')
    message = data.get('message')
    sender_username = data.get('username')
    timestamp = datetime.now(timezone.utc).isoformat()

    if not (room and message and sender_username):
        current_app.logger.error("❌ Room, message, and username are required.")
        return jsonify({"success": False, "message": "Missing room, message, or username"}), 400

    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        # 1) Find the user's uid from raw_user_meta_data->>'username'
        cursor.execute('''
            SELECT id 
            FROM auth.users 
            WHERE raw_user_meta_data->>'username' = %s
        ''', (sender_username,))
        sender_row = cursor.fetchone()
        if not sender_row:
            current_app.logger.error(f"❌ handle_private_message: user '{sender_username}' not found in auth.users")
            return jsonify({"success": False, "message": "Sender user not found"}), 404

        sender_uid = sender_row["id"]

        # 2) Encrypt message
        encrypted = f.encrypt(message.encode()).decode()

        # 3) Insert into public.messages
        cursor.execute('''
            INSERT INTO public.messages (room_name, sender_id, message, timestamp)
            VALUES (%s, %s, %s, %s)
        ''', (room, sender_uid, encrypted, timestamp))
        conn.commit()

        # 4) Emit to everyone in that room
        socketio.emit('private_message', {
            'room': room,
            'username': sender_username,
            'message': message,
            'timestamp': timestamp,
            'sender_id': sender_uid
        }, room=room) # to=room

        return jsonify({"success": True, "message": "Message sent successfully"}), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error storing private message: {e}")
        return jsonify({"success": False, "message": "Failed to store message"}), 500
    finally:
        cursor.close()
        conn.close()


#########################
#  TOPICS
#########################

def join_topic_chat(data):
    topic_name = data.get('topic')
    user_id = data.get('user_id')

    if not topic_name or not user_id:
        current_app.logger.error("❌ Topic name or user_id is missing.")
        return {"success": False, "message": "Topic name and user ID are required."}

    conn = None
    cursor = None
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        # optional: fetch raw_user_meta_data->>'username'
        cursor.execute('''
            SELECT raw_user_meta_data->>'username' AS username
            FROM auth.users
            WHERE uid = %s;
        ''', (user_id,))
        user_row = cursor.fetchone()
        if not user_row or not user_row['username']:
            current_app.logger.error(f"❌ Username not found for user_id: {user_id}")
            return {"success": False, "message": "User not found."}

        username = user_row['username']
        current_app.logger.info(f"✅ User '{username}' joining topic '{topic_name}'.")

        # Example: store participation
        cursor.execute('''
            INSERT INTO public.topic_participants (topic_name, user_id, username)
            VALUES (%s, %s, %s)
            ON CONFLICT (topic_name, user_id) DO NOTHING;
        ''', (topic_name, user_id, username))
        conn.commit()

        return {"success": True, "message": f"User {username} joined topic {topic_name}"}

    except Exception as e:
        current_app.logger.exception(f"❌ Error in join_topic_chat: {e}")
        return {"success": False, "message": "Failed to join topic."}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def send_topic_message(topic, username, message):
    if not all([topic, username, message]):
        current_app.logger.error("❌ Topic, username, or message is missing.")
        return {"success": False, "message": "Topic, username, and message are required."}

    conn = None
    cursor = None
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1) Find the user's uid
        cursor.execute('''
            SELECT id 
            FROM auth.users
            WHERE raw_user_meta_data->>'username' = %s
        ''', (username,))
        row = cursor.fetchone()
        if not row:
            current_app.logger.error(f"❌ send_topic_message: user '{username}' not found in auth.users.")
            return {"success": False, "message": "Sender not found."}

        sender_id = row["id"]

        # 2) Insert into public.messages
        cursor.execute('''
            INSERT INTO public.messages (room_name, sender_id, message, timestamp)
            VALUES (%s, %s, %s, %s);
        ''', (f"topic_{topic}", sender_id, message, timestamp))
        conn.commit()

        current_app.logger.info(f"✅ Message sent in topic '{topic}' by '{username}'.")
        return {"success": True, "message": "Message sent successfully."}

    except Exception as e:
        current_app.logger.exception(f"❌ Error in send_topic_message: {e}")
        return {"success": False, "message": "Failed to send topic message."}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
