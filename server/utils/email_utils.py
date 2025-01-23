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
def send_email(to_email, subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_FROM_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_FROM_EMAIL, to_email, msg.as_string())
            print(f"📧 Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# send email notification
def send_email_notification(to_email, subject, body):
    """
    Send an email notification.

    Args:
        to_email (str): Recipient's email address.
        subject (str): Email subject.
        body (str): HTML email body.

    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    try:
        with SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(GMAIL_ADDRESS, GMAIL_PASSWORD)

            msg = MIMEText(body, 'html')
            msg['Subject'] = subject
            msg['From'] = GMAIL_ADDRESS
            msg['To'] = to_email

            smtp.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
            logging.info(f"📧 Email sent successfully to {to_email}")
            return True
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")
        return False


def generate_added_to_pals_email(contact_username, added_by_email):
    """
    Generate the HTML body for 'added to Pals' email.

    Args:
        contact_username (str): The recipient's username.
        added_by_email (str): The email of the user who added them.

    Returns:
        str: HTML email content.
    """
    login_url = url_for('login_page', _external=True)
    return f"""
    <html>
        <body>
            <h2>Hello {contact_username},</h2>
            <p><strong>{added_by_email}</strong> just added you to their Pals list on BlakeOL!</p>
            <p>Log in now to start chatting:</p>
            <a href="{login_url}" 
               style="color: white; background: #002147; padding: 10px; text-decoration: none; border-radius: 5px;">
               Go to BlakeIM
            </a>
        </body>
    </html>
    """
