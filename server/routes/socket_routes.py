# server/routes/socket_routes.py
from flask_socketio import emit, join_room, leave_room
import logging

# Socket.IO Connection
@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    try:
        decoded = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        logging.info('Client connected')
        request.user = decoded
    except jwt.InvalidTokenError:
        logging.warning('invalid token provided for Socket.IO connection')
        return False

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')


# Join room
@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    username = data.get('username')
    if not room or not username:
        emit('error', {"message": "Invalid room or username"})
        return
    join_room(room)
    logging.info(f"User {username} joined room {room}")


@socketio.on('send_private_message')
def handle_private_message(data):
    room = data.get('room')
    emit('private_message', data, room=room, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    emit('typing', data, broadcast=True)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    emit('stop_typing', data, broadcast=True)
