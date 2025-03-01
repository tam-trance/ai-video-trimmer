Video link: https://www.youtube.com/watch?v=iQ3qyEet3HM

# Video Processor

A user-friendly application for processing videos, generating transcripts, and creating edited versions.

## For Non-Technical Users

### Option 1: Using the Pre-Built Executable

1. Download the latest release from the project page
2. Extract the zip file to a location on your computer
3. Edit the `.env` file to add your API keys (use Notepad or any text editor)
4. Place your videos in the `raw` folder
5. Run `VideoProcessor.exe` for the graphical interface or `VideoProcessor-Simple.exe` for the console version
6. Follow the on-screen instructions

### Option 2: Building the Executable Yourself

1. Make sure Python 3.8 or higher is installed on your system
2. Download or clone this repository
3. Open a command prompt in the project folder
4. Run `python build_executable.py`
5. Once built, you'll find the executables in the `VideoProcessor-Dist` folder
6. Follow the same usage instructions as in Option 1

## For Developers

### Project Structure

- `app.py` - Main GUI application (Tkinter-based)
- `simple_app.py` - Console version of the application
- `main.py` - Core processing logic
- `src/` - Source code modules:
  - `audio/` - Audio processing utilities
  - `llm/` - Language model integration
  - `transcription/` - Whisper transcription functionality
  - `utils/` - Helper functions for JSON and SRT handling
  - `video/` - Video editing functionality
- `build_executable.py` - Script to build the executable
- `create_resources.py` - Script to create splash screen and icon

### Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

### Installation for Development

```
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Troubleshooting

### Common Issues with the Executable

1. **Executable doesn't start**: Check the logs in the `logs` folder for details
2. **Missing DLL error**: Install the Visual C++ Redistributable for Visual Studio 2015-2022
3. **OpenAI API error**: Make sure you've added your API key to the `.env` file
4. **No videos processed**: Ensure your videos are in the `raw` folder and have a supported format (.mp4, .mov, .avi, .mkv)

### When Building from Source

1. **PyInstaller not found**: Run `pip install pyinstaller` to install it
2. **Package not found errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Large executable size**: This is normal due to AI libraries included in the package

## License

[MIT License](LICENSE)
