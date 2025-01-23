# server/server.py
import logging
from flask import Flask
from flask_session import Session
import os
from config import Config
from server import app, socketio
from server.task_scheduler import scheduler
logging.basicConfig(level=logging.DEBUG if Config.DEBUG else logging.INFO)

if __name__ == '__main__':
    logging.info("Starting Flask server...")
    scheduler.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=Config.DEBUG) # 127.0.0.1, DEBUG