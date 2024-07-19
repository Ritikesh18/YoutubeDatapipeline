import requests
import schedule
import time

# Define the function to trigger the fetch_video_details route
def trigger_fetch_video_details():
    url = "http://127.0.0.1:5000/fetch_video_details"  # Update the URL with your Flask app's URL
    # Define the list of channel IDs to fetch video details for
    channels = ["UCrC8mOqJQpoB7NuIMKIS6rQ", "UC4zWG9LccdWGUlF77LZ8toA", "UC-MXxj6WnSPfXS2JQq6M4_A"]
    # Send a POST request with the list of channel IDs
    response = requests.post(url, json={"channels": channels})
    # Print the response from the Flask app
    print(response.json())

# Schedule the task to run every hour
schedule.every().hour.do(trigger_fetch_video_details)

# Infinite loop to run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)  # Sleep for 1 second to avoid high CPU usage
