import json
import os
import re
import logging
from pathlib import Path
from dotenv import load_dotenv
from yt_dlp.utils import DownloadError
from services.transcript import transcription_function
import subprocess
from TikTokApi import TikTokApi
import asyncio
from datetime import datetime
from utils.utilities import ensure_folder_exists, delete_files, process_json_to_txt

# LOGGING
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv(override=True)
TIKTOK_MAX_RESULTS = int(os.getenv('TIKTOK_MAX_RESULTS', 10))  # Ensure it's an int with a default fallback
RAG_FOLDER = os.getenv('RAG_FOLDER')

def fetch_tiktok_data(topic, client, min_likes=0, min_followers=0, specific_words="None"):
    logging.info("Entered fetch TikTok data function.")
    tiktok_data_folder = Path("./data/tiktokData")
    audio_data_folder = Path("./data/audio/tiktok_audio/audio")

    # Ensure folders exist
    ensure_folder_exists(tiktok_data_folder)
    ensure_folder_exists(audio_data_folder)

    # Clean old data
    delete_files(tiktok_data_folder)
    delete_files(audio_data_folder)

    # Fetch videos
    try:
        logging.info(f"Sending request to tiktok api with max results {TIKTOK_MAX_RESULTS} and topic {topic}")
        videos = asyncio.run(fetch_tiktok_videos(topic, int(TIKTOK_MAX_RESULTS)))
    except TimeoutError:
        logging.error("Request timed out")

    if not videos:
        logging.info("No videos fetched.")
        return
    logging.info(f"Fetched videos: {videos}")

    # Process videos with respect to TIKTOK_MAX_RESULTS
    saved_count = 0  # Track the number of saved videos

    for video in videos:
        if saved_count >= TIKTOK_MAX_RESULTS:
            logging.info("saved count reached") ###
            break

        likes = video.get("likes", 0)
        subscribers = video.get("subscribers", 0)
        description = video.get("description", "").lower()  # Normalize case for comparison

        # Check conditions
        meets_likes = likes >= min_likes
        meets_followers = subscribers >= min_followers

        specific_words_list = [word.strip() for word in re.split(r'[、,]', specific_words)]
        # Check if at least one word from `specific_words` is in the description
        if specific_words_list:
            contains_keyword = True if specific_words.lower() == "none" else any(word in description or f"#{word}" in description for word in specific_words_list)
        else:
            contains_keyword = True  # If no words specified, don't filter on this
        logging.info(f"meets_likes: {meets_likes}")
        logging.info(f"meets_followers: {meets_followers}")
        logging.info(f"contains_keyword: {contains_keyword}")

        # Save only if all conditions are met
        if meets_likes and meets_followers and contains_keyword:
            video_id = video.get("video_id", "unknown")
            file_path = tiktok_data_folder / f"{video_id}.json"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(video, f, ensure_ascii=False, indent=4)

            saved_count += 1  # Increase count only when a video is saved

    logging.info(f"Saved {saved_count} videos to {tiktok_data_folder}")

    for filename in os.listdir(tiktok_data_folder):
        if filename.endswith('.json'):
            video_id = filename.split('.')[0]
            try:
                transcription_function(tiktok_data_folder, filename, audio_data_folder, client)
            except DownloadError:
                raise
            except Exception as e:
                raise
            logging.info(f"Process of video {video_id} concluded.")

async def fetch_tiktok_videos(word: str, n: int):
    results = []
    ms_token = os.getenv("MS_TOKEN")
    logging.info("Entered TiktokApi function.")
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser=os.getenv("TIKTOK_BROWSER", "chromium"))
        tag = api.hashtag(name=word)
        async for video in tag.videos(count=n, timeout=60000):

            video_dict = video.as_dict
            channel_id = video_dict.get("author", {}).get("uniqueId", "")
            video_id = video_dict.get("id", "")
            result = {
                "platform": "tiktok",
                "title": None,
                "description": video_dict.get("desc", ""),
                "published_at": datetime.fromtimestamp(video_dict.get("createTime", 0)).isoformat() + "Z",
                "channel": video_dict.get("author", {}).get("nickname", ""),
                "channel_id": channel_id,
                "video_id": video_id,
                "url": f"https://www.tiktok.com/@{channel_id}/video/{video_id}" if channel_id and video_id else "",
                "views": video_dict.get("stats", {}).get("playCount", 0),
                "likes": video_dict.get("stats", {}).get("diggCount", 0),
                "comments": video_dict.get("stats", {}).get("commentCount", 0),
                "shares": video_dict.get("stats", {}).get("shareCount", 0),
                "saves": video_dict.get("stats", {}).get("collectCount", 0),
                "tags": [tag["hashtagName"] for tag in video_dict.get("textExtra", []) if tag.get("type") == 1],
                "subscribers": video_dict.get("authorStats", {}).get("followerCount", 0),
                "total_videos": video_dict.get("authorStats", {}).get("videoCount", 0),
            }
            results.append(result)
    return results

# if __name__ == "__main__":
#     videos = asyncio.run(fetch_tiktok_videos("japan", 30))
#     print(videos)