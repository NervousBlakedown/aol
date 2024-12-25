# email_templates/invite_signup.py

from server.email_utils import send_email
from jinja2 import Template
import os
import sys

# HTML Template for the Invite Signup Email
html_template = """
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>You're Invited to Join BlakeOL</title>
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
        You're Invited to Join BlakeOL, {{ username }}!
      </div>
      <div class="content">
        <p>Hello, {{ username }},</p>
        <p>I'm Blake, creator of BlakeOL, and I'm inviting you
        to join BlakeOL: an instant messaging web app where communication 
        and collaboration come together seamlessly.</p>
        <p>The internet used to feel like an open portal to a world of endless possibilities. Now, it feels anyting but. 
        Because modern tech companies are interested in profit over people, I wanted to build a platform that 
        focuses on user experience and summons a time when talking to friends after school on 
        mom and dad's computer was 
        something exciting-a time when we actually 
        WANTED notifications and didn't growl at them.</p>
        <p>On BlakeOL, there's no tracking, no ads, 100% message encryption, no bots and no costs. We don't compare ourselves to other platforms because, well, frankly, we don't need to.</p>
        <p>Click below to create your account and become part of our growing community. Let me know how I can pray for you and I hope to see you on BlakeOL!</p>
        <a href="https://blakeol.onrender.com/signup" class="cta-button">Join Now</a>
      </div>
      <div class="footer">
        Pax Christi,<br>
        <strong>Blake</strong><br>
        Founder of BlakeOL
      </div>
    </div>
  </body>
</html>
"""

# 📧 Send Invite Signup Email
def send_invite_signup_email(recipient_email: str, username: str):
    """
    Sends an 'Invite to Sign Up' email to a user.
    """
    subject = f"You're Invited to Join BlakeOL"
    body = Template(html_template).render(username=username)
    success = send_email(recipient_email, subject, body, is_html=True)
    
    if success:
        print(f"✅ Email successfully sent to {recipient_email}")
    else:
        print(f"❌ Failed to send email to {recipient_email}. Check logs for details.")


# 🌐 Preview Invite Signup Email
def preview_invite_signup_email(username: str):
    """
    Generates an HTML preview of the 'Invite to Sign Up' email.
    """
    rendered_email = Template(html_template).render(username=username)

    # Define the preview file path in the email_templates directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    preview_file = os.path.join(current_dir, "invite_signup_preview.html")

    with open(preview_file, "w") as file:
        file.write(rendered_email)

    print(f"✅ Preview generated: Open '{preview_file}' in your browser.")


# Command-Line Interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Send or preview 'Invite to Sign Up' email.")
    parser.add_argument(
        '--mode',
        choices=['send', 'preview'],
        required=True,
        help="Choose 'send' to send an email or 'preview' to generate an HTML preview."
    )
    parser.add_argument('--username', required=True, help="Username of the recipient.")
    parser.add_argument('--email', required=True, help="Recipient's email address (required for sending).")

    args = parser.parse_args()

    if args.mode == 'send':
        if not args.email:
            print("❌ Error: --email is required in 'send' mode.")
            sys.exit(1)
        send_invite_signup_email(args.email, args.username)
    elif args.mode == 'preview':
        preview_invite_signup_email(args.username)
