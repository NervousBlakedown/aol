# server/utils/encryption.py
from cryptography.fernet import Fernet
import os

# Load Encryption Key
fernet_key = os.getenv('FERNET_KEY')
f = Fernet(fernet_key.encode())

# Encrypt Data
def encrypt_data(data):
    return f.encrypt(data.encode()).decode()

# Decrypt Data
def decrypt_data(data):
    return f.decrypt(data.encode()).decode()