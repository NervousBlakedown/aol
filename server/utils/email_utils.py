# server/utils/email_utils.py
import smtplib
from config import Config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from dotenv import load_dotenv
from smtplib import SMTP
from flask import url_for
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Send email
def send_email(to_email, subject, message, is_html = False): # is_html = False
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_FROM_EMAIL
    msg["To"] = to_email

    # Attach the email body as HTML or plain text
    if is_html:
        msg = MIMEMultipart()
        msg.attach(MIMEText(message, 'html'))
    else:
        msg.attach(MIMEText(message, 'plain'))

    msg["Subject"] = subject
    msg["From"] = Config.SMTP_FROM_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(Config.SMTP_SERVER, int(Config.SMTP_PORT)) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_FROM_EMAIL, to_email, msg.as_string())
            logger.info(f"📧 Email successfully sent to {to_email}")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}")
        return False


# send email notification
def send_email_notification(to_email, subject, body):
    return send_email(to_email, subject, body, is_html=True)


# "someone added you to their Pals list" email
def generate_added_to_pals_email(contact_username, added_by_email):
    login_url = url_for('login_page', _external=True)
    return f"""
    <html>
        <body>
            <h2>Hello {contact_username},</h2>
            <p><strong>{added_by_email}</strong> just added you to their Pals list on BlakeOL!</p>
            <p>Log in now to start chatting:</p>
            <a href="{login_url}" 
               style="color: white; background: #002147; padding: 10px; text-decoration: none; border-radius: 5px;">
               Go to BlakeOL
            </a>
        </body>
    </html>
    """