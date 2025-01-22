# server/email_templates/pals_notification.py
from server.email_utils import send_email
from jinja2 import Template
import os
import sys

# HTML Template for "You've Been Added to Pals List" Email
html_template = """
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>You've Been Added to a Pals List</title>
    <style>
      .container {
        font-family: Arial, sans-serif;
        max-width: 600px;
        margin: 0 auto;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
      }
      .header {
        background-color: #002147; /* Maastricht Blue */
        color: #ffffff;
        text-align: center;
        padding: 20px;
        font-size: 24px;
      }
      .content {
        padding: 20px;
        color: #444444;
        line-height: 1.6;
      }
      .content p {
        margin-bottom: 15px;
      }
      .cta-button {
        display: inline-block;
        background-color: #002147; /* Maastricht Blue */
        color: #ffffff;
        text-align: center;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 20px;
      }
      .cta-button:hover {
        background-color: #001833;
      }
      .footer {
        font-size: 12px;
        color: #888888;
        text-align: center;
        margin-top: 30px;
        padding: 10px 0;
        border-top: 1px solid #e0e0e0;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        Hello, {{ recipient_username }}!
      </div>
      <div class="content">
        <p>You've just been added to <strong>{{ sender_username }}</strong>'s Pals list on <strong>BlakeOL</strong>!</p>
        <p>Start chatting and reconnect with your new Pal today. You can also explore our exciting Topics feature and join discussions with others.</p>
        
        <a href="https://blakeol.onrender.com/login" class="cta-button">Start Chatting</a>
      </div>
      <div class="footer">
        This is an automated message from BlakeOL. Please do not reply to this email.
      </div>
    </div>
  </body>
</html>
"""

# 📧 Send "Added to Pals" Email
def send_pals_notification_email(recipient_email: str, recipient_username: str, sender_username: str):
    """
    Sends a notification email when someone is added to another user's Pals list.
    """
    subject = f"You've been added to {sender_username}'s Pals list!"
    body = Template(html_template).render(
        recipient_username=recipient_username,
        sender_username=sender_username
    )
    success = send_email(recipient_email, subject, body, is_html=True)
    
    if success:
        print(f"✅ Email successfully sent to {recipient_email}")
    else:
        print(f"❌ Failed to send email to {recipient_email}. Check logs for details.")


# 🌐 Preview "Added to Pals" Email
def preview_pals_notification_email(recipient_username: str, sender_username: str):
    """
    Generates an HTML preview of the 'Added to Pals' email.
    """
    rendered_email = Template(html_template).render(
        recipient_username=recipient_username,
        sender_username=sender_username
    )

    # Define the preview file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    preview_file = os.path.join(current_dir, "pals_notification_preview.html")

    with open(preview_file, "w") as file:
        file.write(rendered_email)

    print(f"✅ Preview generated: Open '{preview_file}' in your browser.")


# 🖥️ Command-Line Interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Send or preview 'Added to Pals' email notification.")
    parser.add_argument(
        '--mode',
        choices=['send', 'preview'],
        required=True,
        help="Choose 'send' to send an email or 'preview' to generate an HTML preview."
    )
    parser.add_argument('--recipient_username', required=True, help="Recipient's username.")
    parser.add_argument('--sender_username', required=True, help="Sender's username.")
    parser.add_argument('--email', help="Recipient's email address (required for sending).")

    args = parser.parse_args()

    if args.mode == 'send':
        if not args.email:
            print("❌ Error: --email is required in 'send' mode.")
            sys.exit(1)
        send_pals_notification_email(args.email, args.recipient_username, args.sender_username)
    elif args.mode == 'preview':
        preview_pals_notification_email(args.recipient_username, args.sender_username)
