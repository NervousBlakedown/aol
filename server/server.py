import asyncio
import websockets
import sqlite3
import http.server
import socketserver
import threading
import os
import json

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
