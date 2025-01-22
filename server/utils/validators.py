# server/utils/validators.py
# Validate Email
def is_valid_email(email):
    return "@" in email and "." in email
