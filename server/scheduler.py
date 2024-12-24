from apscheduler.schedulers.background import BackgroundScheduler
from email_templates.we_miss_you import send_we_miss_you_email
from auth_utils import get_inactive_users
import logging

# Scheduler Job
def send_periodic_we_miss_you_emails():
    try:
        inactive_users = get_inactive_users()
        for user in inactive_users:
            email = user['email']
            username = user['username']
            send_we_miss_you_email(email, username)
        
        logging.info(f"'We Miss You' emails sent to {len(inactive_users)} users.")
    except Exception as e:
        logging.error(f"Failed to send periodic 'We Miss You' emails: {e}")

# Start Scheduler
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_periodic_we_miss_you_emails, 'interval', weeks=1)
    scheduler.start()
    print("Scheduler is running... Press Ctrl+C to stop.")
