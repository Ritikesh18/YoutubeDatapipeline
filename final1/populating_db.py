import googleapiclient.discovery
import sqlite3
import re
from collections import Counter
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from textblob import TextBlob
import json
import pandas as pd
import schedule
import time

# Ensure your API key is correctly set
api_key = 'AIzaSyCHJx5hjT-NN42MQyAgIGcEoS1DHMYqVGs'

# Connect to SQLite database
conn = sqlite3.connect('youtube_channel_data.db')
c = conn.cursor()

# Function to extract keywords
def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    words = [word for word in words if word not in ENGLISH_STOP_WORDS and len(word) > 1]
    return words

# Function to fetch video details for a channel
def fetch_video_details(channel_name, channel_id):
    youtube = googleapiclient.discovery.build(
        'youtube', 'v3', developerKey=api_key)

    # Fetch the list of videos for the channel
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=50,  # Adjust as needed
        order='date'
    )
    response = request.execute()

    for item in response.get('items', []):
        video_id = item['id'].get('videoId')
        if not video_id:
            continue  # Skip if videoId is not present

        title = item['snippet'].get('title', 'No title')
        description = item['snippet'].get('description', 'No description')
        publication_date = item['snippet'].get('publishedAt', 'No date')
        fetch_date = pd.Timestamp.now().strftime('%Y-%m-%d')

        # Fetch video statistics
        stats_request = youtube.videos().list(
            part='statistics',
            id=video_id
        )
        stats_response = stats_request.execute()
        stats = stats_response.get('items', [])[0].get('statistics', {})

        view_count = int(stats.get('viewCount', 0))
        like_count = int(stats.get('likeCount', 0))
        comment_count = int(stats.get('commentCount', 0))

        # Insert raw data into SQLite database
        c.execute('''INSERT INTO raw_videos (channel_id, channel_name, video_id, title, description, view_count, 
                     like_count, comment_count, publication_date, fetch_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (channel_id, channel_name, video_id, title, description, view_count, 
                   like_count, comment_count, publication_date, fetch_date))
        
        # Extract keywords and calculate sentiment
        keywords = extract_keywords(title) + extract_keywords(description)
        keyword_str = ', '.join(keywords)
        sentiment = TextBlob(description).sentiment.polarity
        sentiment_label = 'positive' if sentiment > 0 else 'negative' if sentiment < 0 else 'neutral'

        # Dummy data for monthly trends (You can replace this with actual calculation logic)
        monthly_view_count = json.dumps({fetch_date: view_count})
        monthly_like_count = json.dumps({fetch_date: like_count})
        monthly_comment_count = json.dumps({fetch_date: comment_count})

        # Insert processed insights into SQLite database
        c.execute('''INSERT INTO processed_insights (channel_id, channel_name, video_id, keywords, sentiment, 
                     monthly_view_count, monthly_like_count, monthly_comment_count, processed_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (channel_id, channel_name, video_id, keyword_str, sentiment_label, monthly_view_count, 
                   monthly_like_count, monthly_comment_count, fetch_date))
        
        conn.commit()

# List of channels with names and IDs
channels = {
    "study_iq": {"id": "UCrC8mOqJQpoB7NuIMKIS6rQ", "name": "Study IQ"},
    "amazon_prime_video": {"id": "UC4zWG9LccdWGUlF77LZ8toA", "name": "Amazon Prime Video"},
    "lucky_plays": {"id": "UC-MXxj6WnSPfXS2JQq6M4_A", "name": "Lucky Plays"}
}

# Fetch video details for all channels
for channel_name, channel_info in channels.items():
    fetch_video_details(channel_info["name"], channel_info["id"])

# Close the database connection
schedule.every().hour