# server/services/email_service.py
from server.utils.email_utils import send_email_notification, send_email
# from server.email_templates.added_to_pals_email import generate_added_to_pals_email
from server.email_templates.thank_you_signup import send_thank_you_signup_email
from jinja2 import Template
import logging
logger = logging.getLogger(__name__)


# Wrapper function to send the thank-you email via service layer
def trigger_thank_you_email(recipient_email: str, username: str):
    """
    Trigger the thank-you email by calling the existing email template function.

    Args:
        recipient_email (str): The user's email address.
        username (str): The user's username.
    """
    try:
        send_thank_you_signup_email(recipient_email, username)
        logger.info(f"✅ Thank you email successfully sent to {recipient_email}")
    except Exception as e:
        logger.error(f"❌ Failed to send thank you email to {recipient_email}: {e}")


# Send Notification Email
def send_notification_email(to_email, subject, body):
    try:
        send_email_notification(to_email, subject, body)
        logging.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


# Send missed email
def generate_missed_message_email(username, missed_messages):
    """
    Generate the HTML body for missed message notifications.

    Args:
        username (str): The recipient's username.
        missed_messages (list[dict]): List of missed messages with sender details.

    Returns:
        str: HTML email content.
    """
    message_details = "".join(
        f"<li>{message['sender']} at {message['timestamp']}</li>"
        for message in missed_messages
    )

    return f"""
    <html>
        <body>
            <h2>Hello {username},</h2>
            <p>You have {len(missed_messages)} unread messages on BlakeOL from:</p>
            <ul>
                {message_details}
            </ul>
            <p>Log in now to catch up on your messages:</p>
            <a href="/auth/login" 
               style="color: white; background: #002147; padding: 10px; text-decoration: none; border-radius: 5px;">
               Log In to BlakeIM
            </a>
        </body>
    </html>
    """

