import streamlit as st
import os
from yt_dlp.utils import DownloadError

from analytics.data_fetcher import fetch_social_media_data
from utils.session import is_cookie_uploaded, reset_data_states
from utils.utilities import fetch_graphrag
from ui.components.input_form import FormData

def render_action_buttons(client, form_data: FormData):
    """
    Render action buttons (Fetch Data and Generate Graph).
    
    Args:
        client: OpenAI client instance
        form_data: FormData object containing form inputs
    """
    col1, col2 = st.columns([1, 1]) 
    
    with col1:
        _render_fetch_button(client, form_data)
    
    with col2:
        _render_graph_button()

def _render_fetch_button(client, form_data: FormData):
    """Render the fetch data button and handle its logic."""
    if st.button("Fetch Data", key="fetch_data_button"):
        validation_error = _validate_form_data(form_data)
        if validation_error:
            st.error(validation_error)
            return
        
        reset_data_states()
        
        # Fetch data
        with st.spinner("Crawling and analyzing the video..."):
            try:
                data = fetch_social_media_data(
                    topic=form_data.topic,
                    client=client,
                    platform=form_data.platform,
                    start_date=None,
                    end_date=None,
                    min_likes=form_data.min_likes,
                    min_followers=form_data.min_followers,
                    specific_words=form_data.specific_words,
                    political_perspective=form_data.political_perspective
                )
                st.session_state.fetched_data = data if data else None
                
            except DownloadError:
                st.error("Your cookie.txt file has expired. Please load a new file.")
                st.session_state.fetched_data = None
            except Exception:
                st.error("An error occurred while retrieving data.")
                st.session_state.fetched_data = None

def _render_graph_button():
    """Render the generate graph button and handle its logic."""
    if not _has_fetched_data():
        return
    
    if not st.session_state.get("graph_generated", False):
        if st.button("Generate Graph", key="generate_graph_button"):
            with st.spinner("Generating graph..."):
                rag_folder = os.getenv('RAG_FOLDER')
                fetch_graphrag(
                    st.session_state.data_folder, 
                    os.path.join(rag_folder, "input")
                )
            st.session_state.graph_generated = True
    
    _render_download_button() # for generated graph

def _render_download_button():
    """Render the download button for the generated graph."""
    if not st.session_state.get("graph_generated", False):
        return
    
    rag_folder = os.getenv('RAG_FOLDER')
    rag_graph_path = os.path.join(rag_folder, "output/graph.graphml")
    
    if os.path.exists(rag_graph_path):
        with open(rag_graph_path, "rb") as file:
            st.download_button(
                label="Download the graphml file",
                data=file,
                file_name=os.path.basename(rag_graph_path),
                mime="application/octet-stream"
            )
    else:
        st.write("Graph File does not exist.")

def _validate_form_data(form_data: FormData) -> str:
    """
    Validate form data and return error message if invalid.
    
    Returns:
        str: Error message if validation fails, empty string if valid
    """
    if not is_cookie_uploaded():
        return "The cookie file has not been uploaded or expired. Please upload it."
    
    if not form_data.topic:
        return "Topic not specified, please enter one."
    
    if not form_data.political_perspective:
        return "Political stance not specified, please enter one."
    
    if not form_data.platform:
        return "No platform selected, please choose TikTok or YouTube."
    
    return ""

def _has_fetched_data() -> bool:
    """Check if data has been fetched."""
    return hasattr(st.session_state, 'fetched_data') and st.session_state.fetched_data