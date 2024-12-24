# email_utils.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# Validate environment variables
if not GMAIL_ADDRESS or not GMAIL_PASSWORD:
    raise ValueError("GMAIL_ADDRESS and GMAIL_PASSWORD must be set in your environment variables.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_email(recipient_email: str, subject: str, body: str, is_html: bool = False) -> bool:
    """
    Send an email via SMTP.

    Args:
        recipient_email (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        is_html (bool): Whether the body is HTML or plain text. Default is False.

    Returns:
        bool: True if the email is sent successfully, False otherwise.
    """
    try:
        sender_email = GMAIL_ADDRESS
        password = GMAIL_PASSWORD

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Send email via SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        logger.info(f"Email successfully sent to {recipient_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed. Check your email credentials.")
        return False
    except smtplib.SMTPConnectError:
        logger.error("Failed to connect to the SMTP server.")
        return False
    except smtplib.SMTPException as smtp_error:
        logger.error(f"SMTP error occurred: {smtp_error}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error when sending email: {e}")
        return False
