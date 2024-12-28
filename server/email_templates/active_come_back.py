# email_templates/active_come_back.py
from server.email_utils import send_email
from jinja2 import Template
import os
import sys

# HTML
html_template = """
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Come Back</title>
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
        Thanks for using BlakeOL, {{ username }}!
      </div>
      <div class="content">
        <p>Thanks for using <strong>BlakeOL</strong>! 
        You were active in a Topic chat recently and I just wanted to say you should 
        come back and help continue the conversation! 
        </p>
        
        <p>I'm Blake, creator of BlakeOL. My goal is to build a platform 
        that makes communication feel simple again. 
        My Catholic worldview guides the heart and soul 
        of everything I do, and building meaningful software 
        for people and not profit is part of that. Thanks for signing up for the product, let me 
        know how I can pray for you, and I look forward to seeing you on BlakeOL!</p>
        
        <a href="https://blakeol.onrender.com/login" class="cta-button">Get Started</a>
      </div>
   """

# Send "Come Back" Email
def send_come_back_email(recipient_email: str, username: str):
    """
    Sends a 'Thank You for Signing Up' email to a user.
    """
    subject = f"Thanks for using BlakeOL, {username}!"
    body = Template(html_template).render(username=username)
    success = send_email(recipient_email, subject, body, is_html=True)
    
    if success:
        print(f"✅ Email successfully sent to {recipient_email}")
    else:
        print(f"❌ Failed to send email to {recipient_email}. Check logs for details.")

# Preview Email
def preview_come_back_email(username: str):
    """
    Generates an HTML preview of the 'Thank You for Signing Up' email.
    """
    rendered_email = Template(html_template).render(username=username)

    # Define the preview file path in the email_templates directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    preview_file = os.path.join(current_dir, "come_back.html")

    with open(preview_file, "w") as file:
        file.write(rendered_email)

    print(f"✅ Preview generated: Open '{preview_file}' in your browser.")

# Command-Line Interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Send or preview 'Thank You for Signing Up' email.")
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
            print("❌ Error: --email is required in 'send' mode.")
            sys.exit(1)
        send_come_back_email(args.email, args.username)
    elif args.mode == 'preview':
        preview_thank_you_signup_email(args.username)
