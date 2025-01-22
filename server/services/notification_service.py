# server/services/notification_service.py
from flask import jsonify
from server.utils.db import supabase_client
import logging
from datetime import datetime, timezone

# Create Notification
def create_notification(user_id, message, link=None):
    try:
        conn = supabase_client()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO public.notifications (user_id, message, link, created_at)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, message, link, datetime.now(timezone.utc)))
        conn.commit()
        return {"success": True, "message": "Notification created successfully"}
    except Exception as e:
        logging.error(f"Error creating notification: {e}")
        return {"success": False, "message": "Failed to create notification"}
    finally:
        cursor.close()
        conn.close()

# Get Notifications
def get_notifications(user):
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        user_id = user.get('id')
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, message, link, is_read, created_at
            FROM public.notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10;
        ''', (user_id,))
        notifications = cursor.fetchall()
        return jsonify({"success": True, "notifications": notifications}), 200
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        return jsonify({"success": False, "message": "Failed to fetch notifications"}), 500
    finally:
        cursor.close()
        conn.close()

# Mark Notification as Read
def mark_notification_read(user, notification_id):
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        user_id = user.get('id')
        conn = supabase_client()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE public.notifications
            SET is_read = TRUE
            WHERE id = %s AND user_id = %s;
        ''', (notification_id, user_id))
        conn.commit()
        return jsonify({"success": True, "message": "Notification marked as read"}), 200
    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        return jsonify({"success": False, "message": "Failed to mark notification as read"}), 500
    finally:
        cursor.close()
        conn.close()


# Handle missed notifications
def handle_missed_topic_notification(user_id, topic_id, missed_messages):
    """
    Logs missed topic notifications for a user.
    Args:
        user_id (str): The ID of the user.
        topic_id (str): The ID of the topic.
        missed_messages (int): The count of missed messages.
    """
    try:
        conn = supabase_client()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notifications (user_id, message, link, is_read)
            VALUES (%s, %s, %s, %s)
        ''', (
            user_id,
            f"You missed {missed_messages} messages in Topic {topic_id}.",
            f"/topic/{topic_id}",
            False
        ))

        conn.commit()
        logging.info(f"Missed topic notification logged for user {user_id} on topic {topic_id}.")
    except Exception as e:
        logging.error(f"Error logging missed topic notification: {e}")
    finally:
        cursor.close()
        conn.close()
# Fin
