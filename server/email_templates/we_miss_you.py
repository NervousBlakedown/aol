# email_templates/we_miss_you.py
from server.email_utils import send_email
from jinja2 import Template
import os
import sys

# HTML Template for the "We Miss You" Email
html_template = """
<html>
  <head>
    <style>
      .container {
        font-family: Arial, sans-serif;
        text-align: center;
        background-color: #f9f9f9;
        padding: 20px;
      }
      .header {
        color: #444;
        font-size: 24px;
        margin-bottom: 10px;
      }
      .button {
        display: inline-block;
        background-color: #0078D7;
        color: white;
        padding: 10px 20px;
        text-decoration: none;
        border-radius: 5px;
        margin-top: 20px;
      }
      .footer {
        font-size: 12px;
        color: #888;
        margin-top: 30px;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">We Miss You, {{ username }}!</div>
      <p>We've noticed you haven't been around lately, and we miss you!</p>
      <a href="https://blakeol.onrender.com/login" class="button">Log In Now</a>
      <div class="footer">
        Best regards,<br>
        The BlakeOL Team
      </div>
    </div>
  </body>
</html>
"""

# 📧 Send "We Miss You" Email
def send_we_miss_you_email(recipient_email: str, username: str):
    """
    Sends a "We Miss You" email to a user.
    """
    subject = f"We Miss You, {username}!"
    body = Template(html_template).render(username=username)
    success = send_email(recipient_email, subject, body, is_html=True)
    
    if success:
        print(f"✅ Email successfully sent to {recipient_email}")
    else:
        print(f"❌ Failed to send email to {recipient_email}. Check logs for details.")

# 🌐 Preview "We Miss You" Email
def preview_we_miss_you_email(username: str):
    """
    Generates an HTML preview of the "We Miss You" email.
    """
    rendered_email = Template(html_template).render(username=username)

    # Define the preview file path in the email_templates directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    preview_file = os.path.join(current_dir, "we_miss_you_preview.html")

    with open(preview_file, "w") as file:
        file.write(rendered_email)

    print(f"✅ Preview generated: Open '{preview_file}' in your browser.")


# Command-Line Interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Send or preview 'We Miss You' email.")
    parser.add_argument(
        '--mode',
        choices=['send', 'preview'],
        required=True,
        help="Choose 'send' to send an email or 'preview' to generate an HTML preview."
    )
    parser.add_argument('--username', required=True, help="Username of the recipient.")
    parser.add_argument('--email', help="Recipient's email address (required for sending).")

    args = parser.parse_args()

    if args.mode == 'send':
        if not args.email:
            print("Error: --email is required in 'send' mode.")
            sys.exit(1)
        send_we_miss_you_email(args.email, args.username)
    elif args.mode == 'preview':
        preview_we_miss_you_email(args.username)
