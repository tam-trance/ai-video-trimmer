import os
import json
import sys
from pathlib import Path

# Add parent directory to Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

def format_srt_content(json_data):
    # TODO: Implement the actual SRT formatting logic
    return ""  # Placeholder return

def create_srt_from_json(json_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_name = os.path.splitext(os.path.basename(json_path))[0]

    json_content = json.load(open(json_path))
    srt_content = format_srt_content(json_content)
    
    srt_file = os.path.join(script_dir, "subtitles", f"{base_name}.srt")
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"Saved SRT file to {srt_file}")

if __name__ == "__main__":
    create_srt_from_json("./jsons/IMG_0644_transcription.json") 