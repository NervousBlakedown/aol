# server/task_scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from server.utils.db import supabase_client
from server.utils.email_utils import send_email
from server.routes.notifications_routes import notify_missed_messages
# from email_templates.we_miss_you import send_we_miss_you_email
from server.utils.auth_utils import get_inactive_users
import logging
from datetime import datetime, timedelta

# create scheduler instance at module level
scheduler = BackgroundScheduler()

# 'We miss you' job; send emails to people who haven't logged in for a week
def notify_inactive_users():
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                raw_user_meta_data->>'email' AS email, 
                raw_user_meta_data->>'username' AS username,
                last_sign_in_at 
            FROM auth.users
            WHERE last_sign_in_at < NOW() - INTERVAL '7 days'
        ''')

        inactive_users = cursor.fetchall()

        for user in inactive_users:
            email = user['email']
            username = user['username']

            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>We Miss You, {username}!</h2>
                <p>It's been a while since you last logged in to <strong>BlakeOL</strong>, and we miss having you around.</p>
                <p>Your pals have been active and want to hear from you again!</p>
                <p>
                    <a href="https://blakeol.onrender.com/auth/login" 
                    style="display: inline-block; padding: 10px 20px; color: #fff; background-color: #007bff; 
                    text-decoration: none; border-radius: 5px;">Login to BlakeOL</a>
                </p>
                <p style="color: #999; font-size: 12px;">If you wish to stop receiving these emails, you can update your notification preferences.</p>
            </body>
            </html>
            """

            send_email(email, "We Miss You on BlakeOL!", email_body)

        conn.close()
        logging.info(f"📧 Sent 'We Miss You' emails to {len(inactive_users)} inactive users.")
    except Exception as e:
        logging.error(f"❌ Error sending notifications: {e}")


# Delete old messages from 'messages' table (TODO: can be anything or any date)
def delete_old_messages():
    """Delete messages older than 40 days."""
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM public.messages
            WHERE timestamp < NOW() - INTERVAL '40 days';
        ''')

        conn.commit()
        logging.info(f"✅ Old messages deleted successfully at {datetime.now()}")
    except Exception as e:
        logging.error(f"❌ Error deleting old messages: {e}")
    finally:
        cursor.close()
        conn.close()


# Check unread messages after 24 hours and send email to receiver after they've been sent
def check_and_notify_unread_messages():
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                m.message, 
                m.timestamp, 
                u.raw_user_meta_data->>'email' AS recipient_email, 
                s.raw_user_meta_data->>'username' AS sender_username
            FROM public.messages m
            JOIN auth.users u ON u.id = m.receiver_id
            JOIN auth.users s ON s.id = m.sender_id
            WHERE m.read = FALSE 
            AND m.timestamp < NOW() - INTERVAL '24 hours'
        ''')

        unread_messages = cursor.fetchall()

        for message in unread_messages:
            email = message['recipient_email']
            sender_name = message['sender_username']
            message_content = message['message']

            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Hey there!</h2>
                <p>You have unread messages on <strong>BlakeOL</strong> from <b>{sender_name}</b>.</p>
                <blockquote style="border-left: 4px solid #ccc; padding-left: 10px;">
                    {message_content}
                </blockquote>
                <p>Don't miss out on your conversations. Click below to check your messages.</p>
                <p>
                    <a href="https://blakeol.onrender.com/auth/login" 
                    style="display: inline-block; padding: 10px 20px; color: #fff; background-color: #28a745; 
                    text-decoration: none; border-radius: 5px;">Login to BlakeOL</a>
                </p>
                <p style="color: #999; font-size: 12px;">If you did not request this notification, you can ignore this email.</p>
            </body>
            </html>
            """

            send_email(email, "You have unread messages on BlakeOL", email_body)

        conn.close()
        logging.info(f"📧 Sent notifications for {len(unread_messages)} unread messages.")
    except Exception as e:
        logging.error(f"❌ Error sending notifications: {e}")


# add jobs to scheduler
scheduler.add_job(delete_old_messages, 'interval', days=3)
scheduler.add_job(notify_inactive_users, 'interval', weeks=1)
scheduler.add_job(notify_missed_messages, 'interval', hours=1)
scheduler.add_job(check_and_notify_unread_messages, 'interval', hours=24)

# Start Scheduler
if __name__ == '__main__':
    scheduler.start()
    print("Scheduler is running... Press Ctrl+C to stop.")
    # Prevent script from exiting
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")