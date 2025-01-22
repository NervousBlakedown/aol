# server/socketio_events.py
from server import socketio
from flask_socketio import emit, join_room, leave_room
import logging


# Example Socket.IO Handlers
@socketio.on('connect')
def handle_connect():
    logging.info('Client connected.')


@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected.')


@socketio.on('send_private_message')
def handle_private_message(data):
    room = data['room']
    message = data['message']
    username = data['username']
    emit('private_message', {
        'room': room,
        'username': username,
        'message': message,
    }, room=room)

# start chat
@socketio.on('start_chat')
def handle_start_chat(data):
    room = generate_room_name(data['users'])  # Function to generate room names
    join_room(room)
    emit('chat_started', {'room': room, 'users': data['users']}, to=room)
    logging.info(f"Chat started for room: {room}")

