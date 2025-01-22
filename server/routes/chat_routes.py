# server/routes/chat_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit, join_room
import logging
from server import socketio
from server.services.chat_service import (
    start_chat,
    fetch_chat_history,
    handle_private_message,
    join_topic_chat,
    send_topic_message
)
from datetime import datetime, timezone
from server.utils.db import supabase_client
from server.utils.auth_utils import token_required
chat_bp = Blueprint('chat', __name__)

#########################
#  PRIVATE CHATS
#########################

@chat_bp.route('/start_chat', methods=['POST'])
@token_required
def start_chat_route():
    """
    Expects JSON: { "users": ["bob", "alice"] }
    Returns JSON like { "success": true, "room": "alice_bob" }
    """
    user = request.user  # Extracted from the token
    user_id = user.get('sub')
    chat_partner_id = request.json.get('partner_id')

    if not user:
        current_app.logger.error("No users provided to start_chat_route")
        return jsonify({"success": False, "message": "No users provided"}), 400

    current_app.logger.info(f"Starting chat with users: {user}")
    # The service returns (jsonify(...), status_code)
    resp, status_code = start_chat(user)
    return resp, status_code


# endpoint to handle user search requests
@chat_bp.route('/search_users', methods=['GET'])
def search_users():
    search_query = request.args.get('query', '').strip()
    if not search_query:
        return jsonify({"success": False, "message": "Search query is required."}), 400

    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        
        # Ensure the search query matches usernames
        cursor.execute('''
            SELECT raw_user_meta_data->>'username' AS username 
            FROM auth.users
            WHERE raw_user_meta_data->>'username' ILIKE %s
            LIMIT 20
        ''', (f'%{search_query}%',))

        users = [{"username": row["username"]} for row in cursor.fetchall()]
        current_app.logger.info(f"Users found for query '{search_query}': {users}")

        if not users:
            return jsonify({"success": True, "users": []})

        return jsonify({"success": True, "users": users})

    except Exception as e:
        logging.error(f"Error searching users: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Internal server error"}), 500

    finally:
        cursor.close()
        conn.close()


# Fetch chat history (pulled from chat_service.py)
@chat_bp.route('/get_private_chat_history', methods=['GET'])
def get_private_chat_history():
    room = request.args.get('room')
    if not room:
        return jsonify({"success": False, "message": "Room name is required."}), 400

    try:
        return fetch_chat_history(room)
    except Exception as e:
        logging.error(f"Error fetching chat history: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch chat history"}), 500


# Send message
@chat_bp.route('/send_message', methods=['POST'])
def handle_send_message_route():
    """
    Expects JSON:
    {
      "room": <string>,
      "message": "...",
      "username": "bob"
    }
    """
    data = request.get_json() or {}
    room = data.get('room')
    message = data.get('message')
    username = data.get('username')

    if not room or not message or not username:
        current_app.logger.error("❌ Room, message, and username are required.")
        return jsonify({"success": False, "message": "Room, message, and username are required."}), 400

    socket_data = {
        "room": room,
        "message": message,
        "username": username
    }
    return handle_private_message(socket_data)


#########################
#  TOPIC CHATS
#########################

@chat_bp.route('/send_topic_message', methods=['POST'])
def send_topic_message_route():
    data = request.get_json() or {}
    topic = data.get('topic')
    username = data.get('username')
    message = data.get('message')
    response = send_topic_message(topic, username, message)
    return jsonify(response)


@socketio.on('join_room')
def handle_join_room_socket(data):
    room = data.get('room')
    username = data.get('username')
    join_room(room)
    logging.info(f"User {username} joined room {room}")


@socketio.on('join_topic_chat')
def join_topic_chat_socket(data):
    room = data.get('room')
    user_id = data.get('user_id')
    username = data.get('username')

    if not room or not user_id:
        current_app.logger.error(f"❌ Missing parameters. Room: {room}, User ID: {user_id}")
        emit('error', {'message': 'Room and User ID are required.'})
        return

    try:
        topic_only = room.replace('topic_', '')
        join_topic_chat({"topic": topic_only, "user_id": user_id})
        join_room(room)
        emit('message', {
            'room': room,
            'username': username,
            'message': f'{username} has joined the topic chat.',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=room)
        current_app.logger.info(f"✅ User '{username}' joined topic room '{room}'")

    except Exception as e:
        current_app.logger.exception(f"❌ Error in join_topic_chat_socket: {e}")
        emit('error', {'message': 'Failed to join topic chat.'})


#########################
#  GET TOPIC HISTORY
#########################

@chat_bp.route('/get_topic_history', methods=['GET'])
def get_topic_history():
    topic = request.args.get('topic')
    if not topic:
        return jsonify({"success": False, "error": "Missing topic parameter"}), 400

    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        final_room_name = f"topic_{topic}"

        cursor.execute('''
            SELECT 
                public.messages.message, 
                public.messages.timestamp,
                auth.users.raw_user_meta_data->>'username' AS username
            FROM public.messages
            JOIN auth.users ON public.messages.sender_id = auth.users.id
            WHERE public.messages.room_name = %s
            ORDER BY public.messages.timestamp ASC
        ''', (final_room_name,))

        rows = cursor.fetchall()
        messages = []
        for row in rows:
            messages.append({
                "username": row["username"],
                "message": row["message"],
                "timestamp": row["timestamp"]
            })

        cursor.close()
        conn.close()

        current_app.logger.info(f"✅ Fetched {len(messages)} messages for topic: {topic}")
        return jsonify({"success": True, "messages": messages}), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Unexpected Supabase Error in get_topic_history: {e}")
        return jsonify({"success": False, "error": "Failed to fetch topic history"}), 500
