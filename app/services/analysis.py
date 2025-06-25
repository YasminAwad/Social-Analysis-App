from utils.auth import get_openai_client
import os
import time
import logging
from typing import Dict, List, Any

# LOGGING
logging.basicConfig(
    filename="app.log",  # Log file name
    level=logging.INFO,  # Log level (INFO or higher)
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def send_to_chatgpt(prompt: str, client, model: str = "gpt-4o") -> str:
    """
    Send a prompt to ChatGPT and get a response.
    
    Args:
        prompt: The text prompt to send to ChatGPT
        api_key: OpenAI API key
        model: The model to use (default: gpt-4o)
        
    Returns:
        The response from ChatGPT
    """
    
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant who analyzes political content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  
            max_tokens=800
        )
        
        # Extract and return the response text
        logging.info(f"Request to OpenAI API complete")
        return chat_completion
        
    except Exception as e:
        logging.info(f"Error from OpenAI API: {str(e)}")
        return f"Error from OpenAI API: {str(e)}"
        
def generate_chatgpt_question(post, political_perspective):
    """
    Generate a question to analyze whether video content is positive or negative
    toward the specified political party, including references to specific chunks.
    
    Args:
        post: Dictionary containing video information including transcription chunks
        political_choice: String indicating political leaning ("Left" or "Right")
    
    Returns:
        String containing the formatted question with all transcription chunks
    """
    # Get all transcription chunks
    chunks = post.get('transcription', [])
    chunks_text = ""
    
    # Format each chunk with its number and transcription
    for chunk in chunks:
        chunk_num = chunk.get('segment_number', 0)
        transcription = chunk.get('transcription', 'No transcription available')
        # start_time = round(chunk.get('start_time', 0), 2)
        # end_time = round(chunk.get('end_time', 0), 2)
        
        # chunks_text += f"Chunk {chunk_num} ({start_time}s - {end_time}s): {transcription}\n\n"
        chunks_text += f"Chunk {chunk_num}: {transcription}\n\n"
    
    # Format the complete question
    question = f"""
Please determine whether this content is positive or negative for the specified perspective.
Negative content is content that opposes the perspective.
Positive content is content that supports the perspective.
Which chunks were most helpful in determining whether it was positive or negative?
Please answer in JSON format. Please include the following fields:
- "choice" ("positive" or "negative" or "neutral")
- "main" (list of the most important chunk numbers that support your decision)
- "analysis" (string containing an explanation of your reasoning)

perspective: {political_perspective}
Content chunks:

{chunks_text}
"""
    print(question)
    
    return question