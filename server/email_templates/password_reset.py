# server/email_templates/password_reset.py
from server.email_utils import send_email

def send_password_reset_email(recipient_email, reset_link):
    """
    Sends a password reset email to the user.

    Args:
        recipient_email (str): User's email address.
        reset_link (str): Password reset URL.

    Returns:
        None
    """
    subject = "Reset Your BlakeOL Password"
    body = f"""
    <html>
      <head>
        <style>
          .container {{
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f9f9f9;
            padding: 20px;
          }}
          .button {{
            background-color: #0078D7;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            margin-top: 20px;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <h2>Reset Your Password</h2>
          <p>We've received a request to reset your password.</p>
          <p>If you made this request, click the button below to reset your password:</p>
          <a href="{reset_link}" class="button">Reset Password</a>
          <p>If you didn't request this, please ignore this email.</p>
          <p>Best regards,<br>The BlakeOL Team</p>
        </div>
      </body>
    </html>
    """
    send_email(recipient_email, subject, body)
