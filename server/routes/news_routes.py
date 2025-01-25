# server/routes/news_routes.py (RSS feeds, etc.)
from flask import Blueprint, request, jsonify
import os
import feedparser
import datetime
from server.utils.blakes_thoughts_feed import get_daily_thought

# Create blueprint for news-related routes
news_bp = Blueprint("news", __name__)

# Dictionary mapping sources to their RSS feed URLs
RSS_FEEDS = {
    'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
    'npr': 'https://www.npr.org/rss/rss.php?id=1001',
    'cna': 'https://feeds.feedburner.com/catholicnewsagency/dailynews-vatican',
    'saint': 'https://feeds.feedburner.com/catholicnewsagency/saintoftheday'
}

# Parse
@news_bp.route('/api/news', methods=['GET'])
def fetch_news():
    source = request.args.get('source', 'bbc').lower() # BBC default
    feed_url = RSS_FEEDS.get(source)
    if not feed_url:
            return jsonify({"success": False, "message": "Invalid news source"}), 400

    try:
        feed = feedparser.parse(feed_url)
        # Check for parsing errors or empty entries
        if feed.bozo:
            raise Exception(f"Feed parsing error: {feed.bozo_exception}")
        if not feed.entries:
            return jsonify({"success": False, "message": "No news entries found."}), 500    

        # Extract top 10 headlines
        headlines = [
            {"title": entry.title, "url": entry.link}
            for entry in feed.entries[:10]
        ]
        return jsonify({"success": True, "headlines": headlines})
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return jsonify({"success": False, "message": "Failed to fetch news"}), 500


# Fetch Blake's Deep AF Daily Thoughts n'at
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'utils', 'blakes_thoughts.csv')

def fetch_blakes_thoughts():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    try:
        with open(CSV_FILE_PATH, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['date'] == today:
                    return row['content']
    except FileNotFoundError:
        return "No thoughts available for today."
    except Exception as e:
        return f"Error reading thoughts: {e}"
    return "No thought found for today."


# route to fetch Blake's thoughts (that could take forever)
@news_bp.route('/api/blakes_thoughts', methods=['GET'])
def fetch_blakes_thoughts():
    try:
        daily_thought = get_daily_thought()
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        return jsonify({
            "success": True,
            "date": current_date,
            "thought": daily_thought
        })
    except Exception as e:
        print(f"Error fetching Blake's Thoughts: {e}")
        return jsonify({"success": False, "message": "Failed to fetch Blake's Thoughts"}), 500