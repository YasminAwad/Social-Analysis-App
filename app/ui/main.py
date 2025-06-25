import streamlit as st
import os

from utils.session import is_api_key_valid, get_api_key
from utils.auth import get_openai_client
from utils.utilities import save_txt_file
from ui.components.input_form import render_input_form
from ui.components.action_buttons import render_action_buttons
from ui.components.data_display import render_data_display

def main_display():
    """
    Render the main application display.
    """
    st.title("Youtube Monitoring App")

    if not is_api_key_valid():
        st.info("🔑 Please enter your OpenAI API Key in the sidebar to continue.")
        return

    client = get_openai_client(get_api_key())
    
    form_data = render_input_form()
    
    _handle_cookie_upload()

    render_action_buttons(client, form_data)

    render_data_display()

def _handle_cookie_upload():
    """Handle cookie file upload logic."""
    cookies_folder = os.getenv('COOKIES_FOLDER')
    
    uploaded_file = st.file_uploader("Upload cookie file (.txt)", type=["txt"])
    if uploaded_file:
        try:
            save_txt_file(uploaded_file, cookies_folder)
            st.session_state.cookie_uploaded = True
        except ValueError:
            st.error("The file is not in txt format, please try again.")
            st.session_state.cookie_uploaded = False
        except Exception:
            st.error("An error occurred while uploading file.")
            st.session_state.cookie_uploaded = False