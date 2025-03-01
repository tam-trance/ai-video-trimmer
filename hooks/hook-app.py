from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Only include necessary submodules
hiddenimports = [
    "tkinter",
    "dotenv",
    "pydub",
    "main",
    "src.audio.processing",
    "src.llm.suggestion",
    "src.transcription.whisper",
    "src.utils.json_utils",
    "src.utils.srt_utils",
    "src.video.editor",
]

# Include necessary data files
datas = collect_data_files("src")
