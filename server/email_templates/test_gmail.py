import smtplib

GMAIL_ADDRESS = 'blakecalhoun35@gmail.com'
GMAIL_PASSWORD = 'xqjp nlgp gzuu ffyk'

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.set_debuglevel(1)  # Enable verbose debugging
    server.starttls()
    server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
    print("✅ SMTP Authentication Successful!")
    server.quit()
except smtplib.SMTPAuthenticationError:
    print("❌ SMTP Authentication Failed. Check your email credentials.")
except smtplib.SMTPConnectError:
    print("❌ Failed to connect to SMTP server. Check network/firewall.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
