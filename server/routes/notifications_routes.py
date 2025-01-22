# server/routes/notifications_routes.py
from flask import Blueprint, request, jsonify, session, current_app
from server.services.notification_service import (
    get_notifications,
    mark_notification_read,
    handle_missed_topic_notification
)
from server.utils.db import supabase_client
import logging
notifications_bp = Blueprint('notifications', __name__)


"""# Get Notifications
@notifications_bp.route('/api/get-notifications', methods=['GET'])
def get_notifications_route():
    user = session.get('user')
    
    # Validate User Session
    if not user:
        current_app.logger.warn('Unauthorized access attempt to /api/get-notifications')
        return jsonify({"success": False, "message": "User not logged in."}), 401
    
    try:
        notifications = get_notifications(user)
        
        if notifications is None:
            return jsonify({"success": False, "message": "Failed to fetch notifications."}), 500
        
        if not notifications:
            return jsonify({"success": True, "message": "No new notifications.", "notifications": []}), 200

        return jsonify({"success": True, "notifications": notifications}), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching notifications: {e}")
        return jsonify({"success": False, "message": "An error occurred while fetching notifications."}), 500"""


# Mark Notification as Read
@notifications_bp.route('/api/mark-notification-read', methods=['POST'])
def mark_notification_read_route():
    notification_id = request.json.get('id')
    return mark_notification_read(session.get('user'), notification_id)


# Handle Missed Topic Notification
@notifications_bp.route('/api/handle-missed-topic', methods=['POST'])
def handle_missed_topic():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    topic_id = data.get('topic_id')
    missed_messages = data.get('missed_messages', 0)

    if not topic_id or not missed_messages or missed_messages <= 0:
        return jsonify({"success": False, "message": "Invalid data"}), 400

    user_id = session['user']['id']

    try:
        handle_missed_topic_notification(user_id, topic_id, missed_messages)
        return jsonify({"success": True, "message": "Missed topic logged."}), 200
    except Exception as e:
        logging.error(f"Error in handle_missed_topic: {e}")
        return jsonify({"success": False, "message": "Failed to log missed topic"}), 500


# missed messages
@notifications_bp.route('/notify_missed_messages', methods=['POST'])
def notify_missed_messages():
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        # Fetch missed messages older than 24 hours
        cursor.execute('''
            SELECT 
                m.receiver_id,
                u.raw_user_meta_data->>'username' AS username,
                u.raw_user_meta_data->>'email' AS email,
                ARRAY_AGG(
                    JSON_BUILD_OBJECT(
                        'sender', s.raw_user_meta_data->>'username',
                        'timestamp', m.timestamp
                    )
                ) AS missed_messages
            FROM public.messages m
            JOIN auth.users u ON m.receiver_id = u.id
            JOIN auth.users s ON m.sender_id = s.id
            WHERE m.viewed_at IS NULL AND m.timestamp < NOW() - INTERVAL '24 HOURS'
            GROUP BY m.receiver_id, u.raw_user_meta_data->>'username', u.raw_user_meta_data->>'email';
        ''')
        results = cursor.fetchall()

        # Send emails for each receiver
        for row in results:
            username = row['username']
            email = row['email']
            missed_messages = row['missed_messages']

            subject = "You Have Unread Messages on BlakeOL"
            body = generate_missed_message_email(username, missed_messages)

            send_notification_email(email, subject, body)

        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Notifications sent for missed messages."}), 200
    except Exception as e:
        logging.error(f"Error in notify_missed_messages: {e}")
        return jsonify({"success": False, "message": "Failed to send notifications."}), 500
