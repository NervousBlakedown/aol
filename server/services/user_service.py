# server/services/user_service.py
from flask import jsonify, session
from server.utils.db import supabase_client, mark_email_as_sent
from server.services.email_service import (
    trigger_thank_you_email, 
    send_thank_you_signup_email)
from werkzeug.utils import secure_filename
import os
import logging
import threading
logger = logging.getLogger(__name__)


# handle 'thank you' email post-signup
def handle_post_signup(user_data):
    """
    Handles post-signup actions such as sending a thank-you email.

    Args:
        user_data (dict): User data containing username and email.
    """
    try:
        email = user_data.get('email')
        username = user_data.get('username')
        user_id = user_data.get('id')


        if email and username and user_id:
            if send_thank_you_signup_email(email, username):
                mark_email_as_sent(user_id)
                logger.info(f"✅ Thank you email sent and marked for {email}")
            else:
                logger.error(f"❌ Failed to send email to {email}")
        else:
            logger.error("❌ Missing email or username in user data.")
    except Exception as e:
        logger.error(f"❌ Failed to process post-signup actions: {e}")


# Fetch User Profile
def get_profile(user):
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        user_id = user.get('id')
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT raw_user_meta_data ->> 'username' AS username,
                   raw_user_meta_data ->> 'bio' AS bio,
                   raw_user_meta_data ->> 'avatar_url' AS avatar_url
            FROM auth.users
            WHERE id = %s
        ''', (user_id,))
        user_data = cursor.fetchone()
        return jsonify({"success": True, "profile": user_data}), 200
    except Exception as e:
        logging.error(f"Error fetching profile: {e}")
        return jsonify({"success": False, "message": "Failed to fetch profile"}), 500
    finally:
        cursor.close()
        conn.close()


# Update User Bio
def update_bio(user, bio):
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    if not bio:
        return jsonify({"success": False, "message": "Bio is required"}), 400

    try:
        user_id = user.get('id')
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE auth.users
            SET raw_user_meta_data = jsonb_set(raw_user_meta_data, '{bio}', %s)
            WHERE id = %s
        ''', (bio, user_id))
        conn.commit()
        return jsonify({"success": True, "message": "Bio updated successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating bio: {e}")
        return jsonify({"success": False, "message": "Failed to update bio"}), 500
    finally:
        cursor.close()
        conn.close()


# Upload User Avatar
def upload_avatar(avatar, user):
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    if not avatar:
        return jsonify({"success": False, "message": "No file provided"}), 400

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    filename = secure_filename(avatar.filename)
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "message": "Invalid file type"}), 400

    try:
        user_id = user.get('id')
        avatar_dir = os.path.abspath(os.path.join(os.getcwd(), 'frontend', 'static', 'assets', 'avatars'))
        os.makedirs(avatar_dir, exist_ok=True)
        avatar_path = os.path.join(avatar_dir, f"{user_id}_avatar.{filename.rsplit('.', 1)[1]}")
        avatar.save(avatar_path)

        avatar_url = f"/static/assets/avatars/{os.path.basename(avatar_path)}"
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE auth.users
            SET raw_user_meta_data = jsonb_set(raw_user_meta_data, '{avatar_url}', %s)
            WHERE id = %s
        ''', (avatar_url, user_id))
        conn.commit()
        return jsonify({"success": True, "avatar_url": avatar_url}), 200
    except Exception as e:
        logging.error(f"Error uploading avatar: {e}")
        return jsonify({"success": False, "message": "Failed to upload avatar"}), 500
    finally:
        cursor.close()
        conn.close()


# Create User
def create_user(email, password, username):
    if not email or not password or not username:
        return jsonify({"success": False, "message": "Email, password, and username are required"}), 400

    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO auth.users (email, password, raw_user_meta_data)
            VALUES (%s, %s, %s)
        ''', (email, password, {'username': username}))
        conn.commit()
        return jsonify({"success": True, "message": "Signup successful"}), 201
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return jsonify({"success": False, "message": "Failed to create user"}), 500
    finally:
        cursor.close()
        conn.close()


# Authenticate User
def authenticate_user(email, password):
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, email
            FROM auth.users
            WHERE email = %s AND password = %s
        ''', (email, password))
        user = cursor.fetchone()
        if user:
            session['user'] = {
                'id': user['id'],
                'email': user['email']
            }
            return jsonify({"success": True, "message": "Login successful"}), 200
        else:
            return jsonify({"success": False, "message": "Invalid email or password"}), 401
    except Exception as e:
        logging.error(f"❌ Error authenticating user: {e}")
        return jsonify({"success": False, "message": "Failed to authenticate user"}), 500
    finally:
        cursor.close()
        conn.close()
# Fin
