import streamlit as st

def initialize_session_state():
    """Initialize all session state variables with default values."""
    
    if 'api_key_valid' not in st.session_state:
        st.session_state.api_key_valid = False
    
    if 'fetched_data' not in st.session_state:
        st.session_state.fetched_data = None
    
    if 'data_folder' not in st.session_state:
        st.session_state.data_folder = None
    
    if 'graph_generated' not in st.session_state:
        st.session_state.graph_generated = False
    
    if 'cookie_uploaded' not in st.session_state:
        st.session_state.cookie_uploaded = False
    
    # Initialize previous states for tracking changes
    # if 'previous_states' not in st.session_state:
    #     st.session_state.previous_states = {
    #         'topic': None,
    #         'platform': None,
    #         'start_date': None,
    #         'end_date': None,
    #         'min_likes': None,
    #         'min_followers': None,
    #         'specific_words': None,
    #         'political_perspective': None,
    #         'data': None,
    #         'data_folder': None,
    #         'graph_generated': False,
    #         'cookie_uploaded': False,
    #         'openai_api_key': None,
    #     }

def reset_data_states():
    """Reset data-related states when starting a new fetch."""
    st.session_state.fetched_data = None
    st.session_state.graph_generated = False

def is_api_key_valid():
    """Check if API key is validated."""
    return st.session_state.get('api_key_valid', False)

def get_api_key():
    """Get the validated API key."""
    return st.session_state.get('openai_api_key', '')

def is_cookie_uploaded():
    """Check if cookie file is uploaded."""
    return st.session_state.get('cookie_uploaded', False)