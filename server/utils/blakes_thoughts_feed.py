# server/utils/blakes_thoughts_feed.py
import csv
import datetime
import os

# Define the path to your CSV file
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'utils', 'blakes_thoughts.csv')

def get_daily_thought():
    """
    Reads the CSV file and fetches the thought for the current day.
    Returns today's thought if found, else a default message.
    """
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
