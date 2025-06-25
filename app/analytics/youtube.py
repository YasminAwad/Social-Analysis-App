from dateutil.relativedelta import relativedelta
from yt_dlp.utils import DownloadError
from dotenv import load_dotenv
import json as json_module
import requests
import datetime
import logging
import os
import re

from utils.utilities import delete_files, ensure_folder_exists
from analytics.transcript import transcription_function 

# LOGGING
logging.basicConfig(
    filename="app.log",  # Log file name
    level=logging.INFO,  # Log level (INFO or higher)
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

"""
Queries YouTube for videos with "Trump" or #Trump in the title.
Retrieves videos published within the given date range.
Returns up to 5 results with their title, description, URL, publish date, and channel name.

Note:
The query you are currently using (q parameter in search_params)
searches only the title and tags of the videos, not the description.

If you want to include the description in the search, you might need to fetch video details separately
and check the description manually, as YouTube's API does not directly support searching inside descriptions.
"""

# add checks min follow/likes before transcript 

# send example of saved data, and example of frontend visualization (pdf)

load_dotenv(override=True)
YT_GOOGLE_DEV_API_KEY = os.getenv('YT_GOOGLE_DEV_API_KEY')
YT_MAX_RESULTS = os.getenv('YT_MAX_RESULTS')
RAG_FOLDER = os.getenv('RAG_FOLDER')

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

def fetch_youtube_data(topic, client, start_date, end_date, min_likes, min_followers, specific_words):
    """Fetch YouTube videos information following the indications regarding:
        - topic
        - range date of publication (start date - end date)
        - minum number of likes
        - minum number of followers
        - specific words to be present (at least one) in the title together with the topic

       The videos information is saved inside a json file for each video named <video_id>.json
       and inside the folder ./data/youtubeData

       # TODO: this location will have to change probably to the RAG input folder location
    """

    # Folders Initialization
    
    youtube_data_folder = "./data/youtubeData"
    audio_data_folder = "./data/audio/yt_audio/audio"

    ensure_folder_exists("./data")
    ensure_folder_exists(youtube_data_folder)
    ensure_folder_exists(audio_data_folder)

    delete_files(youtube_data_folder)
    delete_files(audio_data_folder)
    
    # Calculate dates with proper timezone awareness
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_date = now_utc - relativedelta(years=5)
    end_date = now_utc - datetime.timedelta(weeks=1)
    logging.info(f"start date: {start_date}, end date: {end_date}")

    # Format as ISO 8601 strings
    published_after = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    published_before = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    logging.info("Searching for videos given the features.")
    status = video_search(YT_GOOGLE_DEV_API_KEY, SEARCH_URL, topic, specific_words, published_after, published_before, youtube_data_folder, max_results=YT_MAX_RESULTS)
    logging.info("Search finished.")
    if status:
        for filename in os.listdir(youtube_data_folder):
            if filename.endswith('.json'):
                video_id = filename.split('.')[0]
                logging.info(f"Processing video: {video_id}")
                
                video_status = get_video_info(YT_GOOGLE_DEV_API_KEY, VIDEO_URL, youtube_data_folder, filename)
                channel_status = get_channel_info(YT_GOOGLE_DEV_API_KEY, CHANNEL_URL, youtube_data_folder, filename)
                check_status = check_and_delete_invalid_file(os.path.join(youtube_data_folder, filename), min_likes, min_followers)
                if check_status:
                    try:
                        transcription_function(youtube_data_folder, filename, audio_data_folder, client)
                    except DownloadError:
                        raise
                    except Exception as e:
                        raise
                logging.info(f"Process of video {video_id} concluded. Check status: {str(check_status)} / Search status: {str(status)} / Video status: {str(video_status)} / Channel status: {str(channel_status)}")


def check_and_delete_invalid_file(file_path, min_likes, min_followers):
    # Check if the file exists and is a JSON file
    if file_path.endswith('.json') and os.path.exists(file_path):
        try:
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json_module.load(file)
            
            # Extract and convert values
            likes = int(data.get("likes", 0)) if data.get("likes") and data.get("likes").isdigit() else 0
            subscribers = int(data.get("subscribers", 0)) if data.get("subscribers") and data.get("subscribers").isdigit() else 0

            # Check conditions
            if likes < min_likes or subscribers < min_followers:
                logging.info(f"Deleting {file_path}: Likes ({likes}) or Subscribers ({subscribers}) below minimum.")
                os.remove(file_path)  # Uncomment this line to delete the file
                return False
            else:
                logging.info(f"Keeping {file_path}: Likes ({likes}), Subscribers ({subscribers}) meet criteria.")
                return True
        
        except Exception as e:
            logging.error(f"Error processing {file_path} during check of likes/followers: {e}")
    else:
        logging.info(f"Invalid file path: {file_path}")

def video_search(API_KEY, SEARCH_URL, topic, specific_words, published_after, published_before, youtube_data_folder, max_results=YT_MAX_RESULTS):
    # Construct search query 
    # at least one specific_word_query should be present if specific_words is not empty
    # topic must be present as well in the title or hashtag
    # specific_words_list = [word.strip() for word in specific_words.split(',')]
    specific_words_list = [word.strip() for word in re.split(r'[、,]', specific_words)]
    specific_words_query = " OR ".join(specific_words_list) if specific_words_list else ""
    query = f"({topic} OR #{topic}) AND ({specific_words_query} OR #{specific_words_query})" if specific_words_query else f"{topic} OR #{topic}"

    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 10,  
        "order": "date",
        "videoDuration": "short",
        "publishedAfter": published_after,
        "publishedBefore": published_before,
        "key": API_KEY
    }
    
    try:
        response = requests.get(SEARCH_URL, params=search_params)
    except:
        logging.info(f"Error in yt search response: {response}")
    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            video_id = item['id']['videoId']
            video_data = {
                "platform": "youtube",
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "published_at": item["snippet"]["publishedAt"],
                "channel": item["snippet"]["channelTitle"],
                "channel_id": item["snippet"]["channelId"],
                "video_id": video_id
            }

            video_filename = f'{youtube_data_folder}/{video_id}.json'
            with open(video_filename, 'w') as file:
                json_module.dump(video_data, file, indent=4)
            logging.info(f"Data for video {video_id} saved to {video_filename}")
        
        logging.info("Search completed successfully")

        return True
    
    else:
        logging.info("Search API request rejected!")
        return False

def get_video_info(API_KEY, VIDEO_URL, data_folder, filename):
    video_id = filename.split('.')[0]
    video_filepath = os.path.join(data_folder, filename)
    with open(video_filepath, 'r') as file:
        video_data = json_module.load(file)

    # Construct the video URL from the video_id
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    video_details_params = {
        "part": "statistics,snippet",
        "id": video_id,
        "key": API_KEY
    }

    details_response = requests.get(VIDEO_URL, params=video_details_params)
    if details_response.status_code == 200:
        details_data = details_response.json()
        video_details = details_data.get("items", [])[0]
        
        statistics = video_details.get("statistics", {})
        snippet = video_details.get("snippet", {})

        views = statistics.get("viewCount", "None")
        likes = statistics.get("likeCount", "None")
        comments = statistics.get("commentCount", "None")
        saves = statistics.get("favoriteCount", "None")
        shares = "None"  # No shareCount in API response
        tags = snippet.get("tags", [])  # Returns a list of tags
        
        video_data.update({
            "url": video_url,
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "tags": tags 
        })

        with open(video_filepath, 'w') as file:
            json_module.dump(video_data, file, indent=4)
        logging.info(f"Updated video data for {video_id} in {video_filepath}")
        return True

    else:
        logging.info("Video API request rejected!")
        return False

def get_channel_info(API_KEY, CHANNEL_URL, data_folder, filename):
    # Fetch the channel's subscriber count and total video count
    video_id = filename.split('.')[0]
    video_filepath = os.path.join(data_folder, filename)
    with open(video_filepath, 'r') as file:
        video_data = json_module.load(file)

    channel_details_params = {
        "part": "statistics,contentDetails",
        "id": video_data["channel_id"],
        "key": API_KEY
    }
    
    channel_response = requests.get(CHANNEL_URL, params=channel_details_params)
    if channel_response.status_code == 200:
        channel_data = channel_response.json()
        statistics = channel_data.get("items", [])[0]["statistics"]
        
        subscribers = statistics.get("subscriberCount", "None")
        total_videos = statistics.get("videoCount", "None")

        video_data.update({
            "subscribers": subscribers,  # Add subscriber count
            "total_videos": total_videos  # Add total number of videos
        })

        with open(video_filepath, 'w') as file:
            json_module.dump(video_data, file, indent=4)
        logging.info(f"Updated channel data for {video_id} in {video_filepath}")
        return True

    else:
        logging.info("Channel API request rejected!")
        return False