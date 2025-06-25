# auth.py
import openai

def validate_openai_key(api_key: str) -> bool:
    """
    Validates the given OpenAI API key.
    Returns True if valid, False otherwise.
    """
    try:
        client = openai.OpenAI(api_key=api_key)
        client.models.list()  # Light test
        return True
    except Exception:
        return False

def get_openai_client(api_key: str) -> openai.OpenAI:
    """
    Returns a configured OpenAI client using the provided API key.
    Assumes the key is already validated.
    """
    return openai.OpenAI(api_key=api_key)
