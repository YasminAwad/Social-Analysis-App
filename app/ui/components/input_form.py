import streamlit as st
from dataclasses import dataclass
from typing import Optional

@dataclass
class FormData:
    """Data class to hold form input values."""
    topic: str
    platform: Optional[str]
    min_likes: int
    min_followers: int
    specific_words: str
    political_perspective: str

def render_input_form() -> FormData:
    """
    Render the input form and return form data.
    
    Returns:
        FormData: Object containing all form input values
    """
    topic = st.text_input("Topic", key="topic_input")
    
    platform = st.radio(
        "Select Platforms", 
        ["TikTok", "YouTube"], 
        index=None, 
        key="platform_select"
    )
    
    min_likes = st.number_input(
        "Min Likes", 
        min_value=0, 
        value=10, 
        key="min_likes_input"
    )
    
    min_followers = st.number_input(
        "Min Followers", 
        min_value=0, 
        value=10, 
        key="min_followers_input"
    )
    
    specific_words = st.text_area(
        "Keywords (comma separated)", 
        key="specific_words_area"
    )
    
    political_perspective = st.text_area(
        "Perspective", 
        key="political_perspective_area"
    )
    
    return FormData(
        topic=topic,
        platform=platform,
        min_likes=min_likes,
        min_followers=min_followers,
        specific_words=specific_words,
        political_perspective=political_perspective
    )