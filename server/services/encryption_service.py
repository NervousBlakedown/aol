# server/services/encryption_service.py
from cryptography.fernet import Fernet
import logging

# Encrypt Message
def encrypt_message(message, f):
    try:
        return f.encrypt(message.encode()).decode()
    except Exception as e:
        logging.error(f"Error encrypting message: {e}")
        return None

# Decrypt Message
def decrypt_message(encrypted_message, f):
    try:
        return f.decrypt(encrypted_message.encode()).decode()
    except Exception as e:
        logging.error(f"Error decrypting message: {e}")
        return None
