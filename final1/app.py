from flask import Flask, jsonify, request
import googleapiclient.discovery
import sqlite3
import re
from collections import Counter
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from textblob import TextBlob
import json
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

api_key = 'AIzaSyDQgJH1vGuLCzsM2QZIpyKWkfpMkp6ckOc'

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('youtube_channel_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    words = [word for word in words if word not in ENGLISH_STOP_WORDS and len(word) > 1]
    return words

def fetch_video_details(channel_name, channel_id):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)

    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=50,
        order='date'
    )
    response = request.execute()

    conn = get_db_connection()
    c = conn.cursor()

    for item in response.get('items', []):
        video_id = item['id'].get('videoId')
        if not video_id:
            continue
        
        # Check if video_id already exists
        existing_video = c.execute("SELECT video_id FROM raw_videos WHERE video_id = ?", (video_id,)).fetchone()
        if existing_video:
            continue  # Skip insertion if video_id already exists
        
        title = item['snippet'].get('title', 'No title')
        description = item['snippet'].get('description', 'No description')
        publication_date = item['snippet'].get('publishedAt', 'No date')
        fetch_date = pd.Timestamp.now().strftime('%Y-%m-%d')

        stats_request = youtube.videos().list(
            part='statistics',
            id=video_id
        )
        stats_response = stats_request.execute()
        stats = stats_response.get('items', [])[0].get('statistics', {})

        view_count = int(stats.get('viewCount', 0))
        like_count = int(stats.get('likeCount', 0))
        comment_count = int(stats.get('commentCount', 0))

        c.execute('''INSERT INTO raw_videos (channel_id, channel_name, video_id, title, description, view_count, 
                     like_count, comment_count, publication_date, fetch_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (channel_id, channel_name, video_id, title, description, view_count, 
                   like_count, comment_count, publication_date, fetch_date))
        
        keywords = extract_keywords(title) + extract_keywords(description)
        keyword_str = ', '.join(keywords)
        sentiment = TextBlob(description).sentiment.polarity
        sentiment_label = 'positive' if sentiment > 0 else 'negative' if sentiment < 0 else 'neutral'

        monthly_view_count = json.dumps({fetch_date: view_count})
        monthly_like_count = json.dumps({fetch_date: like_count})
        monthly_comment_count = json.dumps({fetch_date: comment_count})

        c.execute('''INSERT INTO processed_insights (channel_id, channel_name, video_id, keywords, sentiment, 
                     monthly_view_count, monthly_like_count, monthly_comment_count, processed_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (channel_id, channel_name, video_id, keyword_str, sentiment_label, monthly_view_count, 
                   monthly_like_count, monthly_comment_count, fetch_date))
        
        conn.commit()
        
    

        

def fetch_data(query):
    conn = get_db_connection()
    data = conn.execute(query).fetchall()
    conn.close()
    return data

def view_count_trends(channel_id):
    # Fetch video details before calculating trends
    fetch_video_details('', channel_id)
    
    query = f"SELECT publication_date, view_count FROM raw_videos WHERE channel_id = '{channel_id}'"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=['Publication Date', 'View Count'])
    df['Publication Date'] = pd.to_datetime(df['Publication Date'])
    df.set_index('Publication Date', inplace=True)
    return df 

@app.route('/videos', methods=['GET'])
def get_videos():
    selected_channel = request.args.get('channel')
    conn = get_db_connection()
    videos = conn.execute('SELECT * FROM raw_videos WHERE channel_name = ?', (selected_channel,)).fetchall()
    conn.close()

    return jsonify([dict(ix) for ix in videos])

@app.route('/insights', methods=['GET'])
def get_insights():
    selected_channel = request.args.get('channel')
    conn = get_db_connection()
    insights = conn.execute('SELECT * FROM processed_insights WHERE channel_name = ?', (selected_channel,)).fetchall()
    conn.close()

    return jsonify([dict(ix) for ix in insights])

@app.route('/wordcloud', methods=['GET'])
def generate_wordcloud():
    selected_channel = request.args.get('channel')
    conn = get_db_connection()
    keywords = conn.execute('SELECT keywords FROM processed_insights WHERE channel_name = ?', (selected_channel,)).fetchall()
    conn.close()

    all_keywords = ' '.join([keyword['keywords'] for keyword in keywords])
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_keywords)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('wordcloud.png')  # Save the image to use in Streamlit
    return jsonify({"status": "success", "message": "WordCloud generated successfully."})

@app.route('/view_count_trends/<channel_id>', methods=['GET'])
def view_count_trends_endpoint(channel_id):
    df = view_count_trends(channel_id)
    return df.to_json()

@app.route('/fetch_video_details', methods=['POST'])
def trigger_fetch_video_details():
    # This route will be called by the scheduler to trigger the fetch_video_details function
    
    # Get the list of channel IDs from the request
    channels = request.json.get('channels', [])
    
    # Check if channels are provided
    if not channels:
        return jsonify({"status": "error", "message": "No channels provided."}), 400
    
    # Call fetch_video_details function for each channel
    for channel_id in channels:
        fetch_video_details(channel_id)
    
    return jsonify({"status": "success", "message": "Video details fetched successfully."})


if __name__ == '__main__':
    app.run(debug=True)
