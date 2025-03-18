import os
import tempfile
from openai import OpenAI
import whisper

# Instantiate the client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    except ImportError:
        pass

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Please set it as an environment variable or in a .env file.")

client = OpenAI(api_key=api_key)

def transcribe_audio_segment(segment_audio_path):
    """Transcribe an audio segment using Whisper via the OpenAI API."""
    with open(segment_audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=f, response_format="json"
        )
    transcript_data = transcript.model_dump()
    return transcript_data.get("text", "")


def transcribe_audio_segment_local_whisper(segment_audio_path):
    device = "cpu"
    model = whisper.load_model("medium").to(device)
    print('segment_audio_path', segment_audio_path)
    transcriptions = model.transcribe(segment_audio_path)    
    transcription = transcriptions["text"]
    return transcription



def transcribe_segments(audio, segments):
    """
    For each detected segment, export its audio to a temporary file and transcribe it.
    Returns a list of dicts with keys: start, end, text.
    """
    transcriptions = []
    for seg in segments:
        start_ms = int(seg["start"] * 1000)
        end_ms = int(seg["end"] * 1000)
        segment_audio = audio[start_ms:end_ms]
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            segment_audio.export(tmp.name, format="wav")
            tmp_path = tmp.name
        text = transcribe_audio_segment_local_whisper(tmp_path)
        os.remove(tmp_path)
        transcriptions.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": text.strip()
        })
    return transcriptions

