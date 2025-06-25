import streamlit as st
from utils.auth import validate_openai_key

def sidebar():
    with st.sidebar:
        st.header("🔐 OpenAI API Key")
        user_api_key = st.text_input("Enter your OpenAI API Key", type="password", key="openai_api_key")

        if st.button("Validate API Key", key="validate_api_button"):
            if validate_openai_key(user_api_key):
                st.session_state.api_key_valid = True
                st.success("API Key validated successfully!")
            else:
                st.session_state.api_key_valid = False
                st.error("Invalid OpenAI API key. Please try again.")