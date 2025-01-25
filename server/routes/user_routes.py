# server/routes/user_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, current_app
from server.services.user_service import get_profile, update_bio, upload_avatar
import logging
import os
import jwt
from supabase import create_client, Client
from server.utils.db import supabase_client
from config import Config
from server.utils.auth_utils import token_required
user_bp = Blueprint('user', __name__)
logger = logging.getLogger(__name__)


# Profile route BEFORE authentication
@user_bp.route('/dashboard', methods=['GET'])
def dashboard_page():
    """Unprotected route that returns profile."""
    return render_template('dashboard.html',
                            username='',
                            bio='',
                            avatar_url='')


# Profile route AFTER authentication (use /dashboard for actual profile view)
@user_bp.route('/profile_data', methods=['GET'])
@token_required
def profile_data():
    """protected route that returns user profile as JSON"""
    try:
        user_id = request.user.get('sub')
        logging.debug(f"decoded JWT user id {user_id}")
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT raw_user_meta_data ->> 'username' AS username,
                   raw_user_meta_data ->> 'bio' AS bio,
                   raw_user_meta_data ->> 'avatar_url' AS avatar_url
            FROM auth.users
            WHERE id = %s
        ''', (user_id,))
        profile_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if not profile_data:
            logging.warning(f"No profile data found for user {user_id}")
            return jsonify({"success": False, "message": "user profile not found"}), 404

        username = profile_data.get('username', 'Guest')
        bio = profile_data.get('bio', 'no bio provided')
        avatar_url = profile_data.get('avatar_url', '/static/assets/avatars/default_avatar.png')

        logging.info(f"loaded profile for user {user_id}, username {username}, sub {request.user['sub']}")
        return jsonify({
            "success": True,
            "username": username,
            "bio": bio,
            "avatar_url": avatar_url
        }), 200

    except Exception as e:
        logging.exception(f"Error fetching profile for user {request.user.get('sub')}: {e}")
        return jsonify({"success": False, "message": "failed to load profile"}), 500


# Get usernames
@user_bp.route('/api/user/get_username', methods=['GET'])
def get_username():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400

    # Fetch username from Supabase
    try:
        query = f"SELECT raw_user_meta_data->>'username' AS username FROM auth.users WHERE id = '{user_id}'"
        result = supabase.execute(query)
        if result['data']:
            username = result['data'][0]['username']
            return jsonify({"success": True, "username": username})
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
  

# Update Bio
@user_bp.route('/update_bio', methods=['POST'])
@token_required
def update_bio_route():
    bio = request.json.get('bio')
    user_id = request.user.get('sub')  # User ID from token
    return update_bio(user_id, bio)


# Get usernames
@user_bp.route('/get_all_usernames', methods=['GET'])
def get_all_usernames():
    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        # Pull both the Supabase user ID and the desired username
        cursor.execute('''
            SELECT 
                id AS user_id,
                raw_user_meta_data ->> 'username' AS username
            FROM auth.users
        ''')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Shape it as a list of { "user_id": "...", "username": "..." }
        users = []
        for row in rows:
            users.append({
                "user_id": row["user_id"],
                "username": row["username"] or "Unknown"
            })

        return jsonify({"success": True, "users": users})
    except Exception as e:
        current_app.logger.exception(f"❌ Error fetching usernames: {e}")
        return jsonify({"success": False, "message": "Failed to fetch usernames"}), 500


# Update user status
@user_bp.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    status = data.get('status')
    if not status:
        return jsonify({"success": False, "message": "Status missing"}), 400
    
    user = request.user  # Extracted from the token #BUG 'request' object has no attribute 'user'
    user_id = user.get('sub')  # User ID from token

    try:
        # Update the user's status in Supabase or other storage
        supabase = supabase_client.get_supabase_client()
        response = supabase.table('users').update({"status": status}).eq("id", user_id).execute()

        if response.error:
            current_app.logger.warning(f"⚠️ Error updating status for user ID {user_id}: {response.error}")
            return jsonify({"success": False, "message": "Failed to update status."}), 500

        return jsonify({"success": True, "message": "Status updated successfully."}), 200
    except Exception as e:
        current_app.logger.exception(f"❌ Error updating status: {e}")
        return jsonify({"success": False, "message": "Failed to update status."}), 500


# add pals
@user_bp.route('/add_pal', methods=['POST'])
@token_required
def add_pal():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400

    try:
        user = request.user  # Extract user from token
        user_id = user.get('sub')

        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()

        # Check if the pal already exists
        cursor.execute('''
            SELECT 1 FROM public.contacts
            WHERE user_id = %s 
            AND contact_id = (
                SELECT id FROM auth.users WHERE raw_user_meta_data->>'username' = %s
            )
        ''', (user_id, username))

        if cursor.fetchone():
            return jsonify({"success": False, "message": "User already in your pals list"}), 409

        # Add pal
        cursor.execute('''
            INSERT INTO public.contacts (user_id, contact_id)
            VALUES (%s, (
                SELECT id FROM auth.users WHERE raw_user_meta_data->>'username' = %s
            ))
        ''', (user_id, username))

        conn.commit()
        return jsonify({"success": True, "message": "Pal added successfully"}), 200

    except Exception as e:
        logging.error(f"Error adding pal: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Failed to add pal"}), 500

    finally:
        cursor.close()
        conn.close()


# Get Pals List from Supabase 
# BUG: change 'pending' to 'accepted' status in 'contacts' table 'status' column when friend request sent
@user_bp.route('/get_pals', methods=['GET'])
@token_required
def get_pals():
    user = request.user  # Extracted from the token
    user_id = user.get('sub')  # Example: User ID stored in the token
    logging.info(f"Fetching pals for user ID {user_id}")

    try:
        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                u.raw_user_meta_data ->> 'username' AS username,
                u.raw_user_meta_data ->> 'avatar_url' AS avatar_url
            FROM public.contacts c
            JOIN auth.users u ON u.id = c.contact_id
            WHERE c.user_id = %s;
        ''', (user_id,))

        pals_records = cursor.fetchall()
        pals_list = []
        for pal in pals_records:
            pals_list.append({
                "username": pal["username"],
                "avatar_url": pal["avatar_url"] or "/static/assets/avatars/default_avatar.png"
            })

        current_app.logger.info(f"✅ Fetched {len(pals_list)} pals for user_id: {user_id}")
        return jsonify({"success": True, "pals": pals_list}), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error fetching pals from DB: {e}")
        return jsonify({"success": False, "message": "Failed to fetch pals list"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Upload Avatar
@user_bp.route('/upload_avatar', methods=['POST'])
@token_required
def upload_avatar_route():
    user_id = request.user.get('sub')
    if 'avatar' not in request.files:
        logging.error("❌ No avatar file provided in the request.")
        return jsonify({"success": False, "message": "no avatar file provided"}), 400

    avatar_file = request.files['avatar']
    if avatar_file.filename == '':
        logging.error("❌ Empty filename received.")
        return jsonify({"success": False, "message": "empty filename"}), 400

    # Ensure avatars directory exists
    avatar_dir = os.path.join(current_app.root_path, 'frontend', 'static', 'assets', 'avatars')
    if not os.path.exists(avatar_dir):
        os.makedirs(avatar_dir)
        logging.info(f"✅ Created directory: {avatar_dir}")

    # Get the file extension of the uploaded file
    file_ext = os.path.splitext(avatar_file.filename)[1].lower()
    new_filename = f"{user_id}{file_ext}"
    save_path = os.path.join(avatar_dir, new_filename)

    # Sanitize the file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    
    if file_ext not in allowed_extensions:
        logging.error(f"❌ Unsupported file extension: {file_ext}")
        return jsonify({"success": False, "message": "Unsupported file format"}), 400    

    try:
        # 1) Save the file physically
        avatar_file.save(save_path)
        current_app.logger.info(f"✅ Saved avatar to {save_path}")

        # 2) Update Supabase's auth.users table
        # We'll store /static/assets/avatars/<filename> as avatar_url
        avatar_url = f"/static/assets/avatars/{new_filename}"

        conn = supabase_client.get_db_connection()
        cursor = conn.cursor()
        # Use jsonb_set to update or add the "avatar_url" key in raw_user_meta_data
        cursor.execute('''
            UPDATE auth.users
            SET raw_user_meta_data = 
                CASE 
                    WHEN raw_user_meta_data ? 'avatar_url' 
                    THEN jsonb_set(raw_user_meta_data, '{avatar_url}', to_jsonb(%s::text), true)
                    ELSE raw_user_meta_data || jsonb_build_object('avatar_url', %s)::jsonb
                END
            WHERE id = %s
        ''', (avatar_url, avatar_url, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        current_app.logger.info(f"✅ Updated avatar_url for user_id={user_id} to {avatar_url}")
        return jsonify({"success": True, "avatar_url": avatar_url}), 200

    except Exception as e:
        current_app.logger.exception(f"❌ Error uploading avatar for user_id={user_id}: {e}")
        return jsonify({"success": False, "message": "Failed to upload avatar"}), 500

# update user settings from 'settings' button
@user_bp.route('/user/update_settings', methods=['POST'])
def update_user_settings():
    """
    Updates user settings such as username, email, notifications, and privacy settings.
    """
    if 'user' not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    data = request.json
    user_id = session['user']['id']
    new_username = data.get('username')
    new_email = data.get('email')
    new_password = data.get('password')
    notifications = data.get('notifications')
    privacy = data.get('privacy')

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE auth.users 
                SET raw_user_meta_data = jsonb_set(raw_user_meta_data, '{username}', %s), 
                    email = %s, 
                    password = crypt(%s, gen_salt('bf')),
                    raw_user_meta_data = jsonb_set(raw_user_meta_data, '{notifications}', %s),
                    raw_user_meta_data = jsonb_set(raw_user_meta_data, '{privacy}', %s)
                WHERE id = %s;
            """, (new_username, new_email, new_password, str(notifications).lower(), privacy, user_id))
            conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Settings updated successfully."})
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({"success": False, "message": "Failed to update settings."}), 500

        
# Logout
@user_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'success': True, 'message': 'Logged out successfully.'})