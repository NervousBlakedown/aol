# server/routes/event_routes.py
from flask import Blueprint, request, jsonify, session
from server.utils.db import get_db_connection
import uuid
import logging

events_bp = Blueprint('events', __name__)
logger = logging.getLogger(__name__)

@events_bp.route('/api/events/create', methods=['POST'])
def create_event():
    """
    Create a new live chat event.
    """
    data = request.json
    title = data.get('title')
    description = data.get('description')
    event_date = data.get('event_date')
    created_by = session.get('user')['id']

    if not (title and description and event_date):
        return jsonify({"success": False, "message": "All fields are required."}), 400

    chat_room = title.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO public.events (title, description, created_by, event_date, chat_room)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (title, description, created_by, event_date, chat_room))
            event_id = cursor.fetchone()[0]
            conn.commit()
        conn.close()
        logger.info(f"✅ Event created: {title}")
        return jsonify({"success": True, "event_id": event_id, "chat_room": chat_room})
    except Exception as e:
        logger.error(f"❌ Error creating event: {e}")
        return jsonify({"success": False, "message": "Failed to create event."}), 500
