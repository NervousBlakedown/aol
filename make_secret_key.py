from cryptography.fernet import Fernet

def main():
    key = Fernet.generate_key().decode()
    print("Your new Fernet key is:", key)
    print("Copy this key into your .env file as FERNET_KEY=<key_here>")

if __name__ == "__main__":
    main()
