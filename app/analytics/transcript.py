from yt_dlp.utils import DownloadError
from dotenv import load_dotenv
import logging
import yt_dlp
import json
import os

# LOGGING
logging.basicConfig(
    filename="app.log",  # Log file name
    level=logging.INFO,  # Log level (INFO or higher)
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv(override=True)
TRANSCRIPTION_MODEL_ID = os.getenv('TRANSCRIPTION_MODEL_ID')
COOKIES_FOLDER = os.getenv('COOKIES_FOLDER')

# Function to download audio from YouTube using yt-dlp command
def download_audio_from_youtube(url, output_path, filename="audio.mp3"):
    logging.info(f"Downloading audio from youtube: {url}")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    audio_file = os.path.join(output_path, filename)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': audio_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    ydl_opts['cookiefile'] = COOKIES_FOLDER

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logging.info(f"Audio downloaded using bestaudio: {audio_file}")
        return audio_file
    except Exception as e:
        logging.warning(f"Primary audio download failed: {e}")

    fallback_file = os.path.join(output_path, "fallback_video.%(ext)s")
    ydl_opts_fallback = {
        'format': '230',  # A low-res video format with audio
        'outtmpl': fallback_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
            ydl.download([url])
        # Rename output file to desired name (yt-dlp may save it with video title)
        for file in os.listdir(output_path):
            if file.endswith(".mp3") and "fallback_video" in file:
                os.rename(os.path.join(output_path, file), audio_file)
                break
        logging.info(f"Audio extracted from fallback video: {audio_file}")
        return audio_file
    except Exception as e:
        logging.error(f"Fallback video download failed: {e}")
        return None

    # except DownloadError as e:
    #     logging.info(f"Download failed: {e}. Possible cause: Expired cookies. Try updating your cookies file.")
    #     raise
    # except Exception as e:
    #     logging.info(f"An unexpected error occurred: {e}")
    #     raise
    

def transcribe_audio_openAI(audio_file_path, client):
    logging.info(f"Making request to openAI for audio file {audio_file_path}")
    audio_file= open(audio_file_path, "rb")
    model = TRANSCRIPTION_MODEL_ID
    logging.info(f"using model: {TRANSCRIPTION_MODEL_ID}")
    transcription = client.audio.transcriptions.create(
        file=audio_file,
        model=model,
        response_format="verbose_json",
        timestamp_granularities=["segment"]
    )
    logging.info(f"OpenAI request completed")

    return transcription

def extract_transcription_data(transcription_verbose):
    logging.info(f"Extracting transcription")
    transcription_data = []
    for segment in transcription_verbose.segments:
        transcription_data.append({
            "segment_number": segment.id,
            "start_time": segment.start,
            "end_time": segment.end,
            "transcription": segment.text
        })
    
    return transcription_data

# Main function
def transcription_function(youtube_data_folder, filename, audio_path, client):
    video_id = filename.split('.')[0]
    json_filepath = os.path.join(youtube_data_folder, f"{video_id}.json")

    if os.path.exists(json_filepath):
        with open(json_filepath, 'r', encoding='utf-8') as f:
            video_data = json.load(f)
    else:
        logging.info(f"Warning: {json_filepath} not found. Creating a new JSON.")
        video_data = {}

    youtube_url = video_data.get("url", "No URL found")

    # Step 1: Download the audio using yt-dlp
    try:
        audio_file = download_audio_from_youtube(youtube_url, audio_path, filename=video_id + ".mp3")
    except DownloadError:
        raise
    except Exception:
        raise

    # Step 2: Get the transcription with segment granularity
    transcription = transcribe_audio_openAI(audio_file + ".mp3", client)
    transcription_data = extract_transcription_data(transcription)
    video_data["transcription"] = transcription_data

    # Step 3: Save the updated JSON
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(video_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Update of transcription in the json file for video: {video_id}")


