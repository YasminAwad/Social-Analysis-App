from dotenv import load_dotenv
import streamlit as st
import datetime
import logging
import time
import json
import os
from openai import OpenAI
import subprocess
import shutil
import csv

# LOGGING
logging.basicConfig(
    filename="app.log",  # Log file name
    level=logging.INFO,  # Log level (INFO or higher)
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv(override=True)
OPENAI_KEY = os.getenv('OPENAI_KEY')
RAG_FOLDER = os.getenv('RAG_FOLDER')

def set_up_graphrag():
    # initialize RAG
    ensure_folder_exists(RAG_FOLDER)
    command = ["graphrag", "init", "--root", RAG_FOLDER] # graphrag init --root ./rag
    result = subprocess.run(command, capture_output=True, text=True)
    logging.info(f"Graphrag initialization output: {result.stdout}")

    env_file = os.path.join(RAG_FOLDER, ".env")

    # Read the current content of the .env file
    with open(env_file, "r") as file:
        lines = file.readlines()

    # Update the API key line
    with open(env_file, "w") as file:
        for line in lines:
            if line.startswith("GRAPHRAG_API_KEY="):
                file.write(f"GRAPHRAG_API_KEY={OPENAI_KEY}\n")
            else:
                file.write(line)

    print(f"Updated {env_file} with the new API key.")

    # move the modified settings.py in the rag folder

    shutil.copy("./files/settings.yaml", os.path.join(RAG_FOLDER, "settings.yaml"))

def load_json_data(directory):
    """
    Load JSON data from files in the specified directory
    """
    data = []
    if not os.path.exists(directory):
        return data
    
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    item = json.load(file)
                    data.append(item)
            except Exception as e:
                st.error(f"Error loading {filename}: {str(e)}")
    
    return data

def update_json_files(data, directory):
    """
    Update JSON files with LLM analysis
    """
    for item in data:
        video_id = item.get("video_id", "unknown")
        file_path = os.path.join(directory, f"{video_id}.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(item, file, indent=4, ensure_ascii=False)
            except Exception as e:
                st.error(f"Error updating {file_path}: {str(e)}")

def get_llm_json_values(llm_output):
    # Parse the JSON
    parsed_data = json.loads(llm_output)

    # Extract the "choice" value
    choice = parsed_data.get("choice")
    main = parsed_data.get("main")
    analysis = parsed_data.get("analysis")

    return choice, main, analysis

def ensure_folder_exists(folder_path):
    """Check if a folder exists; if not, create it."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logging.info(f"Folder '{folder_path}' created.")
    else:
        logging.info(f"Folder '{folder_path}' already exists.")
        
def delete_files(folder):
    # delete files (there might be files from previous calls)
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.info(f'Failed to delete {file_path}. Reason: {e}')

    logging.info(f"Initialization of {folder} complete")

def save_txt_file(uploaded_file, save_path):
    """Save the uploaded file to save_path if it's a valid .txt file."""
    try:
        folder_path = os.path.dirname(save_path)
        ensure_folder_exists(folder_path)
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".txt"):  # Check if it's a txt file
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())  # Save file content
                st.success("File successfully uploaded and saved as cookies.txt")
            else:
                raise ValueError("Invalid file format. Please upload a .txt file.")
    except ValueError as e:
        raise
    except Exception as e:
        raise

def process_json_to_txt(source_folder, destination_folder):
    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    # Process each JSON file in the source folder
    for filename in os.listdir(source_folder):
        if filename.endswith(".json"):
            json_path = os.path.join(source_folder, filename)
            txt_path = os.path.join(destination_folder, filename.replace(".json", ".txt"))
            # csv_path = os.path.join(destination_folder, filename.replace(".json", ".csv"))

            with open(json_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)

            # Extract and concatenate all transcription chunks
            full_transcription = " ".join(chunk["transcription"] for chunk in data.get("transcription", []))

            # Remove the "transcription" list and replace with the full transcription string
            data["transcription"] = full_transcription

            # Write to txt
            with open(txt_path, "w", newline="", encoding="utf-8") as txt_file:
                json.dump(data, txt_file, ensure_ascii=False, indent=4)
                # writer = csv.DictWriter(csv_file, fieldnames=data.keys())
                # writer.writeheader()
                # writer.writerow(data)

            print(f"Processed: {filename} -> {txt_path}")

def fetch_graphrag(source_folder, destination_folder):
    # make sure rag input/output folders are empty
    if os.path.exists(RAG_FOLDER):
        try:
            shutil.rmtree(RAG_FOLDER)
            print(f"Folder '{RAG_FOLDER}' and all its contents have been deleted.")
        except Exception as e:
            print(f"Error while deleting the folder: {e}")
    else:
        print(f"Error: The folder '{RAG_FOLDER}' does not exist.")
    # delete_files(os.path.join(RAG_FOLDER, "input"))
    # delete_files(os.path.join(RAG_FOLDER, "output"))
    ensure_folder_exists(RAG_FOLDER)
    ensure_folder_exists(os.path.join(RAG_FOLDER, "input"))
    ensure_folder_exists(os.path.join(RAG_FOLDER, "output"))
    set_up_graphrag()

    process_json_to_txt(source_folder, destination_folder)
    logging.info("Make of txt completed. Start indexing graphrag.")
    command = ["graphrag", "index", "--root", RAG_FOLDER] 
    result = subprocess.run(command, capture_output=True, text=True)
    logging.info("Graphrag indexing output:", result.stdout)