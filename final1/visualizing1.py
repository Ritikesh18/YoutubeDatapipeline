import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter

# Connect to the SQLite database
conn = sqlite3.connect('youtube_channel_data.db')
c = conn.cursor()

# Function to fetch data from the database
def fetch_data(query):
    c.execute(query)
    data = c.fetchall()
    return data

# Function to calculate trends in view counts over time
def view_count_trends(channel_id):
    query = f"SELECT publication_date, view_count FROM raw_videos WHERE channel_id = '{channel_id}'"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=['Publication Date', 'View Count'])
    df['Publication Date'] = pd.to_datetime(df['Publication Date'])
    df.set_index('Publication Date', inplace=True)
    # print(df)
    return df

# Function to extract top keywords from video titles and descriptions
def top_keywords(channel_id):
    query = f"SELECT keywords FROM processed_insights WHERE channel_id = '{channel_id}'"
    data = fetch_data(query)
    keywords = [word for row in data for word in row[0].split(', ')]
    word_counts = Counter(keywords)
    top_keywords = word_counts.most_common(10)
    return top_keywords

# Function to analyze audience engagement metrics (likes, comments)
def audience_engagement(channel_id):
    query = f"SELECT like_count, comment_count FROM raw_videos WHERE channel_id = '{channel_id}'"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=['Likes', 'Comments'])
    return df

# Function to extract additional insights
def additional_insights(channel_id):
    query = f"SELECT video_id, title, view_count, like_count, comment_count FROM raw_videos WHERE channel_id = '{channel_id}' ORDER BY view_count DESC LIMIT 5"
    top_videos = fetch_data(query)
    
    query = f"SELECT AVG(like_count) AS avg_likes, AVG(comment_count) AS avg_comments FROM raw_videos WHERE channel_id = '{channel_id}'"
    avg_engagement = fetch_data(query)[0]
    
    return top_videos, avg_engagement

# Main function to display the UI
def main():
    st.title('YouTube Channel Analytics Dashboard')
    
    # Sidebar with channel selection
    selected_channel = st.sidebar.selectbox('Select Channel', ['Study IQ', 'Amazon Prime Video', 'Lucky Plays'])
    channel_id = {
        'Study IQ': 'UCrC8mOqJQpoB7NuIMKIS6rQ',
        'Amazon Prime Video': 'UC4zWG9LccdWGUlF77LZ8toA',
        'Lucky Plays': 'UC-MXxj6WnSPfXS2JQq6M4_A'
    }[selected_channel]
    
    # Calculate trends in view counts over time
    st.subheader('Trends in View Counts Over Time')
    df_views = view_count_trends(channel_id)
    st.line_chart(df_views)  # Changed to line chart
    
    # Extract top keywords from video titles and descriptions
    st.subheader('Top Keywords from Video Titles and Descriptions')
    top_keywords_list = top_keywords(channel_id)
    wordcloud_text = ' '.join([word[0] for word in top_keywords_list])
    wordcloud = WordCloud(width=800, height=400, background_color ='white').generate(wordcloud_text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot()  # Display word cloud
    
    # Analyze audience engagement metrics (likes, comments)
    st.subheader('Audience Engagement Metrics (Likes, Comments)')
    df_engagement = audience_engagement(channel_id)
    st.write(df_engagement.describe())
    
    # Extract additional insights
    st.subheader('Additional Insights')
    top_videos, avg_engagement = additional_insights(channel_id)
    
    # Visualize top trending videos
    st.subheader('Top Trending Videos')
    top_videos_df = pd.DataFrame(top_videos, columns=['Video ID', 'Title', 'View Count', 'Like Count', 'Comment Count'])
    st.write(top_videos_df)
    
    # Visualize average engagement rate
    st.subheader('Average Engagement Rate Per Video')
    st.write(f"Average Likes: {avg_engagement[0]}, Average Comments: {avg_engagement[1]}")
    
    # Bar chart for average engagement
    avg_engagement_df = pd.DataFrame({'Metric': ['Likes', 'Comments'], 'Average': [avg_engagement[0], avg_engagement[1]]})
    fig, ax = plt.subplots()
    ax.bar(avg_engagement_df['Metric'], avg_engagement_df['Average'])
    ax.set_ylabel('Count')
    ax.set_title('Average Engagement Rate')
    st.pyplot(fig)

if __name__ == '__main__':
    main()
