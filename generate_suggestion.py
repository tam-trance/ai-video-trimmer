import glob
import json
import os
from datetime import datetime

from src.llm.suggestion import get_llm_suggestion
from src.utils.json_utils import save_json
from src.utils.srt_utils import create_srt_from_json


def find_latest_transcription():
    """Find the most recent *_transcription.json file in the jsons folder."""
    json_pattern = os.path.join("jsons", "*_transcription.json")
    files = glob.glob(json_pattern)
    
    if not files:
        raise FileNotFoundError("No transcription files found in the jsons folder")
    
    # Get the latest file based on modification time
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def generate_suggestion():
    try:
        # Find the latest transcription file
        transcription_file = find_latest_transcription()
        base_name = os.path.basename(transcription_file).replace("_transcription.json", "")
        
        print(f"Found latest transcription file: {transcription_file}")
        
        # Read the transcription file
        with open(transcription_file, 'r', encoding='utf-8') as f:
            transcription = json.load(f)
        
        # Generate suggestion using LLM
        print("Generating suggestion using LLM...")
        suggestion = get_llm_suggestion(transcription)
        
        # Save the suggestion
        suggestion_file = os.path.join("jsons", f"{base_name}_suggestion.json")
        save_json(suggestion, suggestion_file)
        print(f"Saved LLM suggestion to: {suggestion_file}")

        # Create SRT file from the suggestion JSON
        os.makedirs("subtitles", exist_ok=True)
        srt_content = create_srt_from_json(suggestion["filtered_transcription"])
        srt_file = os.path.join("subtitles", f"{base_name}.srt")
        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"Saved SRT file to: {srt_file}")
        
        return suggestion_file
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    os.makedirs("jsons", exist_ok=True)
    generate_suggestion()
