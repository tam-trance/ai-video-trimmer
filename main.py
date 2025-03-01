import glob
import os

from pydub import AudioSegment

from src.audio.processing import detect_segments, extract_audio
from src.llm.suggestion import get_llm_suggestion
from src.transcription.whisper import transcribe_segments
from src.utils.json_utils import save_json
from src.utils.srt_utils import create_srt_from_json
from src.video.editor import create_final_video


def process_video(
    video_path, generate_srt=True, generate_video=True, output_video=None
):
    """
    Process a video file to extract audio, transcribe it, get suggestions, and optionally
    create an SRT file and edited video.

    Args:
        video_path (str): Path to the video file to process
        generate_srt (bool): Whether to generate an SRT subtitle file
        generate_video (bool): Whether to generate an edited video
        output_video (str, optional): Path for the output video. If None, creates in the 'edited' folder.

    Returns:
        bool: True if successful
    """
    print(f"Processing {video_path}")
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Get directory for output - use the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create necessary directories relative to the script directory
    os.makedirs(os.path.join(script_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(script_dir, "jsons"), exist_ok=True)
    os.makedirs(os.path.join(script_dir, "edited"), exist_ok=True)
    os.makedirs(os.path.join(script_dir, "subtitles"), exist_ok=True)

    # Step 1: Extract full audio from the video
    temp_audio_file = os.path.join(script_dir, "audio", f"{base_name}_temp_audio.wav")
    extract_audio(video_path, temp_audio_file)

    # Step 2: Load audio and detect segments based on sound levels
    audio = AudioSegment.from_file(temp_audio_file)
    raw_segments = detect_segments(audio, chunk_ms=100)
    raw_segments_file = os.path.join(
        script_dir, "jsons", f"{base_name}_raw_segments.json"
    )
    save_json(raw_segments, raw_segments_file)
    print(f"Saved raw segments JSON to {raw_segments_file}")

    # Step 3: For each segment, transcribe the audio using Whisper
    raw_transcription = transcribe_segments(audio, raw_segments)
    raw_transcription_file = os.path.join(
        script_dir, "jsons", f"{base_name}_transcription.json"
    )
    save_json(raw_transcription, raw_transcription_file)
    print(f"Saved raw transcription JSON to {raw_transcription_file}")

    os.remove(temp_audio_file)

    # Step 4: Send raw transcription to an LLM for filtering and save suggestion JSON locally
    suggestion = get_llm_suggestion(raw_transcription)
    suggestion_file = os.path.join(script_dir, "jsons", f"{base_name}_suggestion.json")
    save_json(suggestion, suggestion_file)
    print(f"Saved LLM suggestion JSON to {suggestion_file}")

    # Step 5: Create SRT file if requested
    if generate_srt:
        srt_content = create_srt_from_json(suggestion)
        srt_file = os.path.join(script_dir, "subtitles", f"{base_name}.srt")
        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"Saved SRT file to {srt_file}")

    # Step 6: Create the final video if requested
    if generate_video:
        if output_video is None:
            output_video = os.path.join(script_dir, "edited", f"{base_name}_edited.mp4")
        create_final_video(video_path, suggestion, output_video)
        print(f"Saved edited video to {output_video}")

    return True


def main():
    """Process all video files in the 'raw' directory"""
    video_files = glob.glob("raw/*")
    for video_file in video_files:
        if os.path.isfile(video_file) and video_file.lower().endswith(
            (".mp4", ".mov", ".avi", ".mkv")
        ):
            process_video(video_file)


if __name__ == "__main__":
    main()
