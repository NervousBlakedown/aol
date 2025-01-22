# server/services/email_service.py
from server.email_utils import send_email_notification
from server.email_templates.added_to_pals_email import generate_added_to_pals_email
import logging


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

