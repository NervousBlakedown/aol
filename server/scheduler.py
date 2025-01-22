# server/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from server.routes.notifications_routes import notify_missed_messages
from email_templates.we_miss_you import send_we_miss_you_email
from auth_utils import get_inactive_users
import logging
from datetime import datetime, timedelta
from server.utils.db import supabase_client


# 'We miss you' job
def notify_inactive_users():
    inactive_users = get_inactive_users()
    for user in inactive_users:
        email = user.get('email')
        if email:
            send_email(email, subject="We miss you!", body="It's been a while since we last saw you. Come back and check us out!")


# Delete old messages from 'messages' table (TODO: can be anything)
def delete_old_messages():
    """Delete messages older than 30 days."""
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM public.messages
            WHERE timestamp < NOW() - INTERVAL '30 days';
        ''')

        conn.commit()
        logging.info(f"✅ Old messages deleted successfully at {datetime.now()}")
    except Exception as e:
        logging.error(f"❌ Error deleting old messages: {e}")
    finally:
        cursor.close()
        conn.close()


# Start Scheduler
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_old_messages, 'interval', days=3)
    scheduler.add_job(notify_inactive_users, 'interval', weeks=1)
    scheduler.add_job(notify_missed_messages, 'interval', hours=1)
    scheduler.add_job(send_periodic_we_miss_you_emails, 'interval', weeks=1)
    scheduler.start()
    print("Scheduler is running... Press Ctrl+C to stop.")
    # Prevent script from exiting
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")