# server/routes/misc_routes.py
from flask import Blueprint, send_from_directory, jsonify, request, render_template, redirect, url_for, session
import os
import logging
import feedparser
misc_bp = Blueprint('misc', __name__)

# debug: env
@misc_bp.route('/get_env', methods=['GET'])
def get_env():
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'error': 'Environment variables not set'}), 500

    return jsonify({
        'SUPABASE_URL': SUPABASE_URL,
        'SUPABASE_KEY': SUPABASE_KEY
    })


# Static assets
@misc_bp.route('/static/assets/<path:filename>')
def serve_assets(filename):
    asset_path = os.path.join(os.getcwd(), 'frontend', 'static', 'assets')
    return send_from_directory(asset_path, filename)


# Donation Page
@misc_bp.route('/donate', methods=['GET'])
def donation_page():
    return render_template('donation.html')


# Contact Page
@misc_bp.route('/contact', methods=['GET'])
def contact_page():
    return render_template('contact.html')


# About page/"Our Story"
@misc_bp.route('/about', methods=['GET'])
def about_page():
    return render_template('about.html')


# contact form submission
@misc_bp.route('/send_message', methods=['POST'])
def send_message():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    if name and email and subject and message:
        logging.info(f"Message from {name} ({email}): {subject} - {message}")
        return jsonify({"success": True, "message": "Message sent successfully!"})
    return jsonify({"success": False, "message": "Missing fields in the form."}), 400


# Test Video Streaming
@misc_bp.route('/test_video')
def test_video():
    return send_from_directory(os.path.join(os.getcwd(), 'frontend', 'static', 'assets', 'videos'), 'vintage_field.mp4')


# Music player
@misc_bp.route('/api/music', methods=['GET'])
def get_genres():
    sounds_dir = os.path.join(os.getcwd(), 'frontend', 'static', 'assets', 'sounds')
    if not os.path.exists(sounds_dir):
        return jsonify({"success": False, "message": "Sounds directory not found."}), 404

    genres = [d for d in os.listdir(sounds_dir) if os.path.isdir(os.path.join(sounds_dir, d))]
    return jsonify({"success": True, "genres": genres})

@misc_bp.route('/api/music/<genre>', methods=['GET'])
def get_albums(genre):
    sounds_dir = os.path.join(os.getcwd(), 'frontend', 'static', 'assets', 'sounds')
    genre_path = os.path.join(sounds_dir, genre)
    if not os.path.exists(genre_path):
        return jsonify({"success": False, "message": "Genre not found."}), 404

    albums = [d for d in os.listdir(genre_path) if os.path.isdir(os.path.join(genre_path, d))]
    return jsonify({"success": True, "albums": albums})

@misc_bp.route('/api/music/<genre>/<album>', methods=['GET'])
def get_songs(genre, album):
    sounds_dir = os.path.join(os.getcwd(), 'frontend', 'static', 'assets', 'sounds')
    album_path = os.path.join(sounds_dir, genre, album)
    if not os.path.exists(album_path):
        return jsonify({"success": False, "message": "Album not found."}), 404

    songs = [f for f in os.listdir(album_path) if f.endswith('.mp3')]
    return jsonify({"success": True, "songs": songs})