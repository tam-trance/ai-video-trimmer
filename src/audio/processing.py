import webrtcvad
from moviepy.editor import VideoFileClip
from pydub import AudioSegment


def extract_audio(video_path, audio_path):
    """Extract audio from video file."""
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, logger=None)
    video.close()

def detect_segments(
    audio,
    frame_duration_ms=30,
    padding_duration_ms=300,
    aggressiveness=3,
    post_speech_padding_sec=0.2,
    **kwargs,
):
    """
    Detect speech segments using voice activity detection (VAD) via webrtcvad,
    with an adjustable post-speech padding to determine the exact cut.
    """
    # Allow backward compatibility with 'chunk_ms'
    if "chunk_ms" in kwargs:
        frame_duration_ms = kwargs["chunk_ms"]

    # webrtcvad only supports frame durations of 10, 20, or 30 ms.
    if frame_duration_ms not in (10, 20, 30):
        print(f"Warning: frame_duration_ms {frame_duration_ms} is invalid. Using 30 ms instead.")
        frame_duration_ms = 30

    # Ensure audio is mono and at a supported sample rate.
    audio = audio.set_channels(1)
    if audio.frame_rate not in (8000, 16000, 32000, 48000):
        audio = audio.set_frame_rate(16000)
    sample_rate = audio.frame_rate
    sample_width = audio.sample_width  # bytes per sample (typically 2 for 16-bit PCM)
    raw_audio = audio.raw_data

    vad = webrtcvad.Vad(aggressiveness)
    # Calculate frame size in samples and then in bytes.
    frame_size = int(sample_rate * frame_duration_ms / 1000)
    frame_bytes = frame_size * sample_width

    # Split raw audio into frames of exact length.
    frames = []
    for i in range(0, len(raw_audio) - frame_bytes + 1, frame_bytes):
        frame = raw_audio[i : i + frame_bytes]
        timestamp = i / (sample_rate * sample_width)
        frames.append((timestamp, frame))

    # Label each frame using VAD.
    speech_flags = []
    for timestamp, frame in frames:
        try:
            is_speech = vad.is_speech(frame, sample_rate)
        except Exception as e:
            print(f"Error processing frame at {timestamp:.2f} sec: {e}")
            is_speech = False
        speech_flags.append((timestamp, is_speech))

    # Aggregate contiguous speech frames into segments
    segments = []
    segment_start = None
    last_speech_timestamp = None
    for timestamp, is_speech in speech_flags:
        if is_speech:
            if segment_start is None:
                segment_start = round(timestamp, 2)  # Round to 2 decimal places
            last_speech_timestamp = timestamp
        else:
            if segment_start is not None and last_speech_timestamp is not None:
                segments.append({
                    "start": round(segment_start, 2),  # Round to 2 decimal places
                    "end": round(last_speech_timestamp + post_speech_padding_sec, 2),  # Round to 2 decimal places
                })
                segment_start = None
                last_speech_timestamp = None
    if segment_start is not None:
        total_duration = len(raw_audio) / (sample_rate * sample_width)
        segments.append({
            "start": round(segment_start, 2),  # Round to 2 decimal places
            "end": round(total_duration, 2)  # Round to 2 decimal places
        })

    # Merge segments that are separated by less than padding_duration_ms.
    merged_segments = []
    if segments:
        current = segments[0]
        for seg in segments[1:]:
            if seg["start"] - current["end"] < padding_duration_ms / 1000.0:
                current["end"] = round(seg["end"], 2)  # Round to 2 decimal places
            else:
                merged_segments.append(current)
                current = seg
        merged_segments.append(current)

    return merged_segments
