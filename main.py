import glob
import os

from pydub import AudioSegment

from src.audio.processing import detect_segments, extract_audio
from src.llm.suggestion import get_llm_suggestion
from src.transcription.whisper import transcribe_segments
from src.utils.json_utils import save_json
from src.utils.srt_utils import create_srt_from_json
from src.video.editor import create_final_video


def process_video(video_path):
    print(f"Processing {video_path}")
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Create necessary directories
    os.makedirs("audio", exist_ok=True)
    os.makedirs("jsons", exist_ok=True)
    os.makedirs("edited", exist_ok=True)
    os.makedirs("subtitles", exist_ok=True)

    # Step 1: Extract full audio from the video
    temp_audio_file = os.path.join("audio", f"{base_name}_temp_audio.wav")
    extract_audio(video_path, temp_audio_file)

    # Step 2: Load audio and detect segments based on sound levels
    audio = AudioSegment.from_file(temp_audio_file)
    raw_segments = detect_segments(audio, chunk_ms=100)
    raw_segments_file = os.path.join("jsons", f"{base_name}_raw_segments.json")
    save_json(raw_segments, raw_segments_file)
    print(f"Saved raw segments JSON to {raw_segments_file}")

    # Step 3: For each segment, transcribe the audio using Whisper
    raw_transcription = transcribe_segments(audio, raw_segments)
    raw_transcription_file = os.path.join("jsons", f"{base_name}_transcription.json")
    save_json(raw_transcription, raw_transcription_file)
    print(f"Saved raw transcription JSON to {raw_transcription_file}")

    os.remove(temp_audio_file)

    # Step 4: Send raw transcription to an LLM for filtering and save suggestion JSON locally
    suggestion = get_llm_suggestion(raw_transcription)
    suggestion_file = os.path.join("jsons", f"{base_name}_suggestion.json")
    save_json(suggestion, suggestion_file)
    print(f"Saved LLM suggestion JSON to {suggestion_file}")

    # Step 5: Create SRT file from the suggestion JSON
    srt_content = create_srt_from_json(suggestion)
    srt_file = os.path.join("subtitles", f"{base_name}.srt")
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"Saved SRT file to {srt_file}")

    # Step 6: Create the final video using segments from the suggestion JSON
    create_final_video(video_path, suggestion)


def main():
    video_files = glob.glob("raw/*")
    for video_file in video_files:
        if os.path.isfile(video_file) and video_file.lower().endswith(
            (".mp4", ".mov", ".avi", ".mkv")
        ):
            process_video(video_file)


if __name__ == "__main__":
    main()
