import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.srt_utils import create_srt_from_json


def create_srt_from_json_wrapper(json_path, srt_file=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    # print('basename', os.path.splitext(os.path.basename(json_path))[0])

    json_content = json.load(open(json_path))
    srt_content = create_srt_from_json(json_content)
    
    if not srt_file:
        srt_file = os.path.join(script_dir, "subtitles", f"{base_name}.srt")
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"Saved SRT file to {srt_file}")


if __name__ == "__main__":
    #create_srt_from_json_wrapper("./jsons/IMG_0644_transcription.json")

    json_path = "/Users/tamtran/Documents/devy/00_repos/VideoEditing/Take10/transcripts/IMG_0644_transcript2.json"
    srt_file = "/Users/tamtran/Documents/devy/00_repos/VideoEditing/Take10/transcripts/IMG_0644_transcript2.srt"
    create_srt_from_json_wrapper(json_path, srt_file)