# server/server.py
import logging
from flask import Flask
from flask_session import Session
import os
from config import Config
from threading import Thread
from server import app, socketio
from server.task_scheduler import scheduler, check_new_users
logging.basicConfig(level=logging.DEBUG if Config.DEBUG else logging.INFO)


# start background user check
def start_user_check_thread():
    thread = Thread(target=check_new_users, daemon=True)
    thread.start()
    logging.info("✅ Background thread started for checking new users.")

# run
if __name__ == '__main__':
    logging.info("Starting Flask server...")
    scheduler.start()
    start_user_check_thread()
    socketio.run(app, host='0.0.0.0', port=5000, debug=Config.DEBUG) # 127.0.0.1, DEBUG