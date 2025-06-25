import streamlit as st
from typing import List, Dict, Any
from utils.utilities import get_llm_json_values

def render_data_display():
    """Render the fetched data display section."""
    if not _has_fetched_data():
        if hasattr(st.session_state, 'fetched_data') and st.session_state.fetched_data is None:
            st.write("No data available.")
        return
    
    data = st.session_state.fetched_data
    st.write("### Data obtained:")
    
    for index, item in enumerate(data, start=1):
        _render_video_item(item, index)

def _render_video_item(item: Dict[str, Any], index: int):
    """Render a single video item with its analysis and information."""
    video_title = item.get('title') or f"Video {index}"
    choice, main, analysis = get_llm_json_values(item.get('llm_analysis', 'No analysis available'))
    
    st.write(f"📹 **{video_title}**")
    _render_sentiment_indicator(choice)

    _render_analysis_section(choice, main, analysis, item)

    _render_video_info_section(item)
    
    _render_transcription_section(item)

def _render_sentiment_indicator(choice: str):
    """Render the sentiment indicator based on analysis choice."""
    if choice == "positive":
        st.success("positive")
    elif choice == "negative":
        st.error("negative")
    elif choice == "neutral":
        st.info("neutral")
    else:
        st.info(choice)

def _render_analysis_section(choice: str, main: List[int], analysis: str, item: Dict[str, Any]):
    """Render the analysis section with relevant transcription chunks."""
    with st.expander("📊 analysis"):
        st.write(f"**Analysis results (those that are in line with the political stance are positive, those that are against are negative, and those that are neutral are neutral):** {choice}")
        
        important_transcriptions = _get_important_transcriptions(item, main)
        
        st.write("**Transcript chunk relevant to political stance:**")
        st.write("\n".join(important_transcriptions) if important_transcriptions else "None")
        st.write(f"**Analysis details:** {analysis}")

def _render_video_info_section(item: Dict[str, Any]):
    """Render the video information section."""
    with st.expander("📜 Video Information"):
        st.write(f"**Posted by:** {item.get('channel', 'N/A')}")
        st.write(f"**Number of followers:** {item.get('subscribers', 'N/A')}")
        st.write(f"**Total videos posted:** {item.get('total_videos', 'N/A')}")
        st.write(f"**Posted on:** {item.get('published_at', 'N/A')}")
        st.write(f"**Summary:** {item.get('description', 'No description available')}")
        st.write(f"**Tags:** {item.get('tags', 'N/A')}")
        st.write(f"**Likes:** {item.get('likes', 'N/A')}")
        st.write(f"**Comments:** {item.get('comments', 'N/A')}")
        st.write(f"**[Views]({item.get('url', '#')})**")

def _render_transcription_section(item: Dict[str, Any]):
    """Render the transcription chunks section."""
    with st.expander("🧩 Transcription Chunks"):
        st.write(item.get('transcription', 'N/A'))

def _get_important_transcriptions(item: Dict[str, Any], main: List[int]) -> List[str]:
    """Extract important transcription chunks based on main segment numbers."""
    transcription_list = item.get('transcription', [])
    return [
        f"{round(chunk['start_time'], 1)} - {round(chunk['end_time'], 1)}: {chunk['transcription']}\n\n"
        for chunk in transcription_list 
        if chunk['segment_number'] in main
    ]

def _has_fetched_data() -> bool:
    """Check if data has been fetched."""
    return hasattr(st.session_state, 'fetched_data') and st.session_state.fetched_data