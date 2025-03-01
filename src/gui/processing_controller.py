"""
Processing Controller for Video Processing Application

This module handles the step-by-step processing of video files:
1. Raw segment detection
2. Transcription
3. LLM Suggestions
4. SRT generation and video editing
"""

import logging
import os
from pathlib import Path

from pydub import AudioSegment

# Import processing functions
from src.audio.processing import detect_segments, extract_audio
from src.llm.suggestion import get_llm_suggestion
from src.transcription.whisper import transcribe_segments
from src.utils.json_utils import load_json, save_json
from src.utils.srt_utils import create_srt_from_json
from src.video.editor import create_final_video


class ProcessingController:
    """Controller class for managing the step-by-step video processing workflow"""

    def __init__(self, app_dir):
        """Initialize the processing controller

        Args:
            app_dir: Application directory for saving output files
        """
        self.app_dir = app_dir

        # Create necessary directories
        self.dirs = {
            "audio": os.path.join(app_dir, "audio"),
            "jsons": os.path.join(app_dir, "jsons"),
            "subtitles": os.path.join(app_dir, "subtitles"),
            "edited": os.path.join(app_dir, "edited"),
        }

        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)

        # Processing state tracking
        self.video_path = None
        self.base_name = None
        self.audio_file = None
        self.segments_file = None
        self.transcription_file = None
        self.suggestion_file = None
        self.srt_file = None
        self.output_video = None

        # Logging callback
        self.log_callback = None

        # Default parameters for segment detection
        self.segment_params = {
            "frame_duration_ms": 30,
            "padding_duration_ms": 300,
            "aggressiveness": 3,
            "post_speech_padding_sec": 0.2,
        }

    def set_callback(self, callback_func):
        """Set the logging callback function

        Args:
            callback_func: Function to call for UI logging
        """
        self.log_callback = callback_func

    def log_info(self, message):
        """Log an informational message

        Args:
            message: Message to log
        """
        logging.info(message)
        if self.log_callback:
            self.log_callback(message)

    def log_warning(self, message):
        """Log a warning message

        Args:
            message: Message to log
        """
        logging.warning(message)
        if self.log_callback:
            self.log_callback(f"WARNING: {message}")

    def set_video_path(self, video_path):
        """Set the video path and derive related file paths"""
        self.video_path = video_path
        self.base_name = os.path.splitext(os.path.basename(video_path))[0]

        # Update file paths
        self.audio_file = os.path.join(
            self.dirs["audio"], f"{self.base_name}_temp_audio.wav"
        )
        self.segments_file = os.path.join(
            self.dirs["jsons"], f"{self.base_name}_raw_segments.json"
        )
        self.transcription_file = os.path.join(
            self.dirs["jsons"], f"{self.base_name}_transcription.json"
        )
        self.suggestion_file = os.path.join(
            self.dirs["jsons"], f"{self.base_name}_suggestion.json"
        )
        self.srt_file = os.path.join(self.dirs["subtitles"], f"{self.base_name}.srt")
        self.output_video = os.path.join(
            self.dirs["edited"], f"{self.base_name}_edited.mp4"
        )

    def update_segment_params(
        self,
        frame_duration_ms=None,
        padding_duration_ms=None,
        aggressiveness=None,
        post_speech_padding_sec=None,
    ):
        """Update segment detection parameters"""
        if frame_duration_ms is not None:
            self.segment_params["frame_duration_ms"] = frame_duration_ms
        if padding_duration_ms is not None:
            self.segment_params["padding_duration_ms"] = padding_duration_ms
        if aggressiveness is not None:
            self.segment_params["aggressiveness"] = aggressiveness
        if post_speech_padding_sec is not None:
            self.segment_params["post_speech_padding_sec"] = post_speech_padding_sec

    def check_dependencies(self):
        """Check which processing steps have been completed

        Returns:
            dict: Status of each processing step
        """
        return {
            "video_selected": self.video_path is not None
            and os.path.exists(self.video_path),
            "segments_detected": (
                os.path.exists(self.segments_file) if self.segments_file else False
            ),
            "transcription_complete": (
                os.path.exists(self.transcription_file)
                if self.transcription_file
                else False
            ),
            "suggestion_complete": (
                os.path.exists(self.suggestion_file) if self.suggestion_file else False
            ),
            "srt_generated": os.path.exists(self.srt_file) if self.srt_file else False,
            "video_generated": (
                os.path.exists(self.output_video) if self.output_video else False
            ),
        }

    def process_raw_segments(self, progress_callback=None):
        """Detect raw speech segments in the video

        Args:
            progress_callback: Function to call with progress updates

        Returns:
            str: Path to the saved segments JSON file
        """
        if progress_callback:
            progress_callback("Extracting audio...")

        # Extract audio from video
        extract_audio(self.video_path, self.audio_file)

        if progress_callback:
            progress_callback("Loading audio file...")

        # Load audio as AudioSegment
        audio = AudioSegment.from_file(self.audio_file)

        if progress_callback:
            progress_callback("Detecting speech segments...")

        # Detect segments with user parameters
        segments = detect_segments(
            audio,
            frame_duration_ms=self.segment_params["frame_duration_ms"],
            padding_duration_ms=self.segment_params["padding_duration_ms"],
            aggressiveness=self.segment_params["aggressiveness"],
            post_speech_padding_sec=self.segment_params["post_speech_padding_sec"],
        )

        # Save segments
        save_json(segments, self.segments_file)

        if progress_callback:
            progress_callback(f"Saved raw segments to {self.segments_file}")

        return self.segments_file

    def process_transcription(self, progress_callback=None):
        """Transcribe the detected segments

        Args:
            progress_callback: Function to call with progress updates

        Returns:
            str: Path to the saved transcription JSON file
        """
        if not os.path.exists(self.segments_file):
            if progress_callback:
                progress_callback(
                    "Error: Raw segments not found. Please detect segments first."
                )
            return None

        if progress_callback:
            progress_callback("Loading audio and segments...")

        # Load audio and segments
        audio = AudioSegment.from_file(self.audio_file)
        segments = load_json(self.segments_file)

        if progress_callback:
            progress_callback("Transcribing audio segments...")

        # Transcribe segments
        transcription = transcribe_segments(audio, segments)

        # Save transcription
        save_json(transcription, self.transcription_file)

        if progress_callback:
            progress_callback(f"Saved transcription to {self.transcription_file}")

        return self.transcription_file

    def process_suggestions(self, progress_callback=None):
        """Generate LLM suggestions based on the transcription

        Args:
            progress_callback: Function to call with progress updates

        Returns:
            str: Path to the saved suggestions JSON file
        """
        if not os.path.exists(self.transcription_file):
            if progress_callback:
                progress_callback(
                    "Error: Transcription not found. Please transcribe segments first."
                )
            return None

        if progress_callback:
            progress_callback("Loading transcription...")

        # Load transcription
        transcription = load_json(self.transcription_file)

        if progress_callback:
            progress_callback("Processing with LLM...")

        # Get LLM suggestions
        suggestion = get_llm_suggestion(transcription)

        # Save suggestion
        save_json(suggestion, self.suggestion_file)

        if progress_callback:
            progress_callback(f"Saved suggestions to {self.suggestion_file}")

        return self.suggestion_file

    def generate_srt(self, progress_callback=None):
        """Generate SRT file from suggestions

        Args:
            progress_callback: Function to call with progress updates

        Returns:
            str: Path to the saved SRT file
        """
        if not os.path.exists(self.suggestion_file):
            if progress_callback:
                progress_callback(
                    "Error: Suggestions not found. Please generate suggestions first."
                )
            return None

        if progress_callback:
            progress_callback("Loading suggestions...")

        # Load suggestions
        suggestion = load_json(self.suggestion_file)

        if progress_callback:
            progress_callback("Generating SRT file...")

        # Create SRT content
        srt_content = create_srt_from_json(suggestion)

        # Save SRT file
        with open(self.srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)

        if progress_callback:
            progress_callback(f"Saved SRT file to {self.srt_file}")

        return self.srt_file

    def generate_edited_video(self, progress_callback=None):
        """Generate edited video from suggestions

        Args:
            progress_callback: Function to call with progress updates

        Returns:
            str: Path to the saved video file
        """
        if not os.path.exists(self.suggestion_file):
            if progress_callback:
                progress_callback(
                    "Error: Suggestions not found. Please generate suggestions first."
                )
            return None

        if progress_callback:
            progress_callback("Loading suggestions...")

        # Load suggestions
        suggestion = load_json(self.suggestion_file)

        if progress_callback:
            progress_callback("Creating edited video...")

        # Create final video
        output_path = create_final_video(self.video_path, suggestion, self.output_video)

        if progress_callback:
            progress_callback(f"Saved edited video to {output_path}")

        return output_path

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.audio_file and os.path.exists(self.audio_file):
            try:
                os.remove(self.audio_file)
                return True
            except Exception as e:
                logging.error(f"Error removing temp audio file: {e}")
                return False
        return False

    def set_segment_params(
        self,
        frame_duration,
        speech_threshold,
        min_speech_duration,
        min_silence_duration,
    ):
        """Set the segment detection parameters

        Args:
            frame_duration: Duration in ms of each audio frame to analyze
            speech_threshold: Percentage of frames that must contain speech
            min_speech_duration: Minimum duration in ms for a speech segment
            min_silence_duration: Minimum duration in ms of silence to separate segments
        """
        self.segment_params = {
            "frame_duration": frame_duration,
            "speech_threshold": speech_threshold,
            "min_speech_duration": min_speech_duration,
            "min_silence_duration": min_silence_duration,
        }

        self.log_info(f"Updated segment detection parameters")
        return self.segment_params
