
from dotenv import load_dotenv
import streamlit as st
import os

from ui.sidebar import sidebar
from ui.main import main_display
from utils.session import initialize_session_state

load_dotenv(override=True)

def main():

    initialize_session_state()

    sidebar()
    
    main_display()

if __name__ == "__main__":
    # streamlit run app.py
    main()
