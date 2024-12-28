from apscheduler.schedulers.background import BackgroundScheduler
from email_templates.we_miss_you import send_we_miss_you_email
from auth_utils import get_inactive_users
import logging

# 'We miss you' job
def notify_inactive_users():
    inactive_users = get_inactive_users()
    for user in inactive_users:
        email = user.get('email')
        if email:
            send_email(email, subject="We miss you!", body="It's been a while since we last saw you. Come back and check us out!")

# Start Scheduler
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_periodic_we_miss_you_emails, 'interval', weeks=1)
    scheduler.start()
    print("Scheduler is running... Press Ctrl+C to stop.")
