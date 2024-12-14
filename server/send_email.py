# server/send_email.py
# sends welcome email after signing up
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Function to send email
def send_email(user_email):
    # Load email credentials from .env
    sender_email = os.getenv("GMAIL_ADDRESS")
    sender_password = os.getenv("GMAIL_PASSWORD")
    if not sender_email or not sender_password:
        raise ValueError("Gmail credentials not set in .env")
    receiver_email = user_email

    # Set up email content
    message = MIMEMultipart("alternative")
    message["Subject"] = "Welcome to BlakeOL"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Create the plain-text and HTML versions of the message
    text = """\
    Hi,
    Thanks for creating a BlakeOL account! I hope you have fun with a nostalgic experience of real-time messaging."""
    html = """\
    <html>
    <body>
        <p>Hi,<br>
        <strong>Thank you for creating a BlakeOL account!</strong>
        </p>
    </body>
    </html>
    """

    # Turn these into MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Attach the parts to the message
    message.attach(part1)
    message.attach(part2)

    # Send the email using SMTP_SSL
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")
