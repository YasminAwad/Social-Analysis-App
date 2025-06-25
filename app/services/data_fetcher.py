import streamlit as st
import time
import os
from typing import List, Dict, Any, Optional
from yt_dlp.utils import DownloadError

from utils.utilities import load_json_data, update_json_files
from services.analysis import generate_chatgpt_question, send_to_chatgpt
from services.youtube import fetch_youtube_data
from services.tiktok import fetch_tiktok_data

def fetch_social_media_data(
    topic: str,
    client,
    platform: str,
    start_date: Optional[str],
    end_date: Optional[str],
    min_likes: int,
    min_followers: int,
    specific_words: str,
    political_perspective: str
) -> List[Dict[str, Any]]:
    """
    Fetch social media data from selected platforms and add LLM analysis.
    
    Args:
        topic: The topic to search for
        client: OpenAI client instance
        platform: Platform to fetch from ("TikTok" or "YouTube")
        start_date: Start date for search (YouTube only)
        end_date: End date for search (YouTube only)
        min_likes: Minimum number of likes
        min_followers: Minimum number of followers
        specific_words: Specific keywords to search for
        political_perspective: Political perspective for analysis
    
    Returns:
        List of dictionaries containing the fetched and analyzed data
    
    Raises:
        DownloadError: If there's an issue with downloading content
        Exception: For other errors during data fetching
    """
    collected_data = []
    
    # Fetch data based on platform
    if platform == "TikTok":
        collected_data = _fetch_tiktok_data(topic, client, min_likes, min_followers, specific_words)
    elif platform == "YouTube":
        collected_data = _fetch_youtube_data(topic, client, start_date, end_date, min_likes, min_followers, specific_words)
    
    # Add LLM analysis to each item
    _add_llm_analysis(collected_data, political_perspective, client)
    
    # Update JSON files with analysis
    if collected_data and hasattr(st.session_state, 'data_folder'):
        update_json_files(collected_data, st.session_state.data_folder)
    
    return collected_data

def _fetch_tiktok_data(topic: str, client, min_likes: int, min_followers: int, specific_words: str) -> List[Dict[str, Any]]:
    """Fetch data from TikTok."""
    st.session_state.data_folder = "./data/tiktokData"
    
    try:
        fetch_tiktok_data(topic, client, min_likes, min_followers, specific_words)
        return load_json_data(st.session_state.data_folder)
    except (DownloadError, Exception):
        raise

def _fetch_youtube_data(
    topic: str, 
    client, 
    start_date: Optional[str], 
    end_date: Optional[str], 
    min_likes: int, 
    min_followers: int, 
    specific_words: str
) -> List[Dict[str, Any]]:
    """Fetch data from YouTube."""
    st.session_state.data_folder = "./data/youtubeData"
    
    try:
        fetch_youtube_data(topic, client, start_date, end_date, min_likes, min_followers, specific_words)
        return load_json_data(st.session_state.data_folder)
    except (DownloadError, Exception):
        raise

def _add_llm_analysis(data: List[Dict[str, Any]], political_perspective: str, client) -> None:
    """
    Add LLM analysis to each data item.
    
    Args:
        data: List of data items to analyze
        political_perspective: Political perspective for analysis
        client: OpenAI client instance
    """
    llm_model_id = os.getenv('LLM_MODEL_ID')
    
    for item in data:
        # Generate question for ChatGPT
        question = generate_chatgpt_question(item, political_perspective)
        item["chatgpt_question"] = question
        
        # Get LLM analysis if client is available
        if client:
            try:
                response = send_to_chatgpt(question, client, llm_model_id)
                response_content = response.choices[0].message.content
                cleaned_response = response_content.strip("```json").strip("```").strip()
                item["llm_analysis"] = cleaned_response
                
                # Add delay to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                item["llm_analysis"] = f"Error: {str(e)}"
        else:
            item["llm_analysis"] = "ChatGPT analysis not enabled"