import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('youtube_channel_data.db')
c = conn.cursor()

# Create raw_videos table
c.execute('''
CREATE TABLE IF NOT EXISTS raw_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    video_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    publication_date TEXT,
    fetch_date TEXT
)
''')

# Create processed_insights table
c.execute('''
CREATE TABLE IF NOT EXISTS processed_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    keywords TEXT,
    sentiment TEXT,
    monthly_view_count TEXT,
    monthly_like_count TEXT,
    monthly_comment_count TEXT,
    processed_date TEXT,
    FOREIGN KEY (video_id) REFERENCES raw_videos(video_id)
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()
