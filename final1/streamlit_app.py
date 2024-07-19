import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# Dictionary of channel names and corresponding channel IDs
channel_dict = {
    "Study IQ": "UCrC8mOqJQpoB7NuIMKIS6rQ",
    "Amazon Prime Video": "UC4zWG9LccdWGUlF77LZ8toA",
    "Lucky Plays": "UC-MXxj6WnSPfXS2JQq6M4_A"
}

st.title("YouTube Channel Data")

# Dropdown for selecting the channel
selected_channel = st.sidebar.selectbox('Select Channel', list(channel_dict.keys()))
channel_id = channel_dict[selected_channel]

st.header("View Count Trends")

if st.button("Plot View Count Trends"):
    response = requests.get(f'http://127.0.0.1:5000/view_count_trends/{channel_id}')
    if response.status_code == 200:
        st.success("View count trends fetched successfully.")
        df = pd.read_json(response.text)
        st.line_chart(df)
    else:
        st.error("Failed to fetch view count trends.")

st.header("View Raw Video Data")
if st.button("Load Raw Video Data"):
    response = requests.get(f'http://127.0.0.1:5000/videos?channel={selected_channel}')
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.error("Failed to load raw video data.")

st.header("View Processed Insights")
if st.button("Load Processed Insights"):
    response = requests.get(f'http://127.0.0.1:5000/insights?channel={selected_channel}')
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.error("Failed to load processed insights.")

st.header("Keywords WordCloud")
if st.button("Generate WordCloud"):
    response = requests.get(f'http://127.0.0.1:5000/wordcloud?channel={selected_channel}')
    if response.status_code == 200:
        st.success("WordCloud generated successfully.")
        img = Image.open('wordcloud.png')
        st.image(img)
    else:
        st.error("Failed to generate WordCloud.")
