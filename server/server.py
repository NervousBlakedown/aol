import asyncio
import websockets
import sqlite3
import http.server
import socketserver
import threading
import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
# from websocket_server import WebsocketServer

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('db/db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

# Signup page (GET request)
@app.route('/signup', methods=['GET'])
def signup_page():
    return send_from_directory('frontend', 'signup.html')

# Signup page (POST request)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    username = data['username']
    password = data['password']  # In real applications, hash passwords!

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if username or email already exists
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        return jsonify({'success': False, 'message': 'Username or email already exists!'})

    # Insert the new user into the database
    cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                   (email, username, password))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

# To serve static assets (like CSS, JS, sounds)
@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('frontend/assets', filename)

# Route to serve the login page
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

connected_users = set()

# Handle WebSocket connections
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
    msg_data = json.dumps({
        'type': 'message',
        'username': data['username'],
        'message': data['message']
    })
    for user in connected_users:
        if user != sender:
            await user.send(msg_data)

async def broadcast_typing(data, sender, is_typing):
    typing_data = json.dumps({
        'type': 'typing' if is_typing else 'stop_typing',
        'username': data['username']
    })
    for user in connected_users:
        if user != sender:
            await user.send(typing_data)

# Start the WebSocket server
async def start_websocket_server():
    server = await websockets.serve(handle_socket_connection, "127.0.0.1", 8080)
    print("WebSocket server started on ws://127.0.0.1:8080")
    await server.wait_closed()

# Serve the static HTML/CSS/JS files using Python's built-in HTTP server
def start_http_server():
    os.chdir("C:\\Users\\blake\\Documents\\github\\aol\\frontend") 
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", 8000), handler)
    print("HTTP server started on http://127.0.0.1:8000")
    httpd.serve_forever()

# Run both servers concurrently using threading and asyncio
def main():
    # Start the HTTP server in a separate thread
    http_thread = threading.Thread(target=start_http_server)
    http_thread.daemon = True  # Ensures the thread exits when the main program exits
    http_thread.start()

    # Start the WebSocket server using asyncio
    asyncio.run(start_websocket_server())

if __name__ == "__main__":
    main()
