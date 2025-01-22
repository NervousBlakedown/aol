# server/server.py
import logging
from flask import Flask
from flask_session import Session
import os
from config import Config
from server import app, socketio
logging.basicConfig(level=logging.DEBUG if Config.DEBUG else logging.INFO)

if __name__ == '__main__':
    # from server import app, socketio  # Delay import to avoid circular dependencies
    logging.info("Starting Flask server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=Config.DEBUG) # 127.0.0.1, DEBUG