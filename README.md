# Video Editor

This application processes videos by extracting audio, detecting speech segments, transcribing them, and creating a filtered version based on LLM suggestions.

## Setup

1. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your API keys in the `.env` file:
     ```
     OPENAI_API_KEY=sk-your-openai-key-here
     GOOGLE_API_KEY=AIzaSy-your-google-key-here
     ```
   - Need help? Join our community at [The AI Forge](https://www.skool.com/the-ai-forge/about)

## Project Structure

```
video-editor/
├── src/
│   ├── audio/
│   │   ├── __init__.py
│   │   └── processing.py      # Audio extraction and VAD
│   ├── transcription/
│   │   ├── __init__.py
│   │   └── whisper.py        # Whisper-based transcription
│   ├── llm/
│   │   ├── __init__.py
│   │   └── suggestion.py     # LLM-based filtering
│   ├── video/
│   │   ├── __init__.py
│   │   └── editor.py         # Video manipulation
│   └── utils/
│       ├── __init__.py
│       └── json_utils.py     # JSON utilities
├── main.py                   # Main script for full video processing
├── generate_suggestion.py    # Script for generating suggestions from existing transcriptions
├── requirements.txt          # Dependencies
└── README.md                # This file
```

## Usage

### Full Video Processing
1. Place your input videos in the `raw/` directory
2. Run the script:
```bash
python main.py
```

### Generate Suggestions Only
If you already have transcription files and just want to generate new suggestions and captions:
```bash
python generate_suggestion.py
```
This script will:
1. Find the latest `*_transcription.json` file in the `jsons/` directory
2. Generate a new suggestion using the LLM
3. Create both a suggestion JSON file and an SRT subtitle file
4. Note: This script does not generate the final video, it only produces suggestions and captions

## Output Structure
The script creates several directories:
- `audio/`: Temporary audio files
- `jsons/`: JSON files containing raw segments, transcriptions, and suggestions
- `edited/`: Final edited videos
- `subtitles/`: SRT subtitle files

## Community Support
Need help or want to join our community? Visit [The AI Forge](https://www.skool.com/the-ai-forge/about) for support and discussions.
