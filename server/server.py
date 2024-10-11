import asyncio
import websockets
import sqlite3
import json
from flask import Flask, request, jsonify, send_from_directory
import bcrypt
import os
import logging
logging.basicConfig(level = logging.DEBUG)

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('db/db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

# Serve static files or index.html by default
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Signup route for GET requests (serves the signup page)
@app.route('/signup', methods=['GET'])
def signup_page():
    return send_from_directory(app.static_folder, 'signup.html')

# Signup route for POST requests (handles account creation)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    username = data['username']
    password = data['password']

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        return jsonify({'success': False, 'message': 'Username or email already exists!'})

    try:
        cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                       (email, username, hashed_password))
        conn.commit()
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'message': 'Error occurred while creating account.'})
    finally:
        conn.close()

    return jsonify({'success': True})

# Login route
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

        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                return jsonify({'success': True, 'message': 'Login successful!'})
            else:
                return jsonify({'success': False, 'message': 'Invalid password.'})
        else:
            return jsonify({'success': False, 'message': 'User not found.'})
    except Exception as e:
        # Log or handle the error as needed
        print("Error during login:", e)
        return jsonify({'success': False, 'message': 'An error occurred during login.'})
    finally:
        # Always close the connection
        conn.close()
    logging.debug("Login attempt finished.")

connected_users = set()

async def handle_socket_connection(websocket, path):
    connected_users.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'message':
                await broadcast_message(data, websocket)
            elif data['type'] == 'typing':
                await broadcast_typing(data, websocket, is_typing=True)
            elif data['type'] == 'stop_typing':
                await broadcast_typing(data, websocket, is_typing=False)
    finally:
        connected_users.remove(websocket)

async def broadcast_message(data, sender):
    msg_data = json.dumps({'type': 'message', 'username': data['username'], 'message': data['message']})
    for user in connected_users:
        if user != sender:
            await user.send(msg_data)

async def broadcast_typing(data, sender, is_typing):
    typing_data = json.dumps({'type': 'typing' if is_typing else 'stop_typing', 'username': data['username']})
    for user in connected_users:
        if user != sender:
            await user.send(typing_data)

async def start_websocket_server():
    async with websockets.serve(handle_socket_connection, "127.0.0.1", 8080):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(start_websocket_server())
