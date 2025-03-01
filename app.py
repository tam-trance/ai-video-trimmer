import logging
import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

# Get the application directory (where the .exe is located)
if getattr(sys, "frozen", False):
    # We're running in a PyInstaller bundle
    APP_DIR = os.path.dirname(sys.executable)
else:
    # We're running in a normal Python environment
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Add APP_DIR to sys.path to ensure imports work properly
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Set up logging
log_dir = os.path.join(APP_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir, f"app_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Add console handler for debugging
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s: %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


# Log uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupts
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )
    # Create an error message box
    error_msg = (
        f"An error occurred: {exc_value}\n\nSee log file for details: {log_file}"
    )
    try:
        import tkinter.messagebox

        tkinter.messagebox.showerror("Application Error", error_msg)
    except:
        # If tkinter isn't working, at least print to stderr
        print(error_msg, file=sys.stderr)


sys.excepthook = handle_exception

# Log startup information
logging.info("=" * 50)
logging.info(f"Application starting. Python version: {sys.version}")
logging.info(f"Working directory: {os.getcwd()}")
logging.info(f"Application directory: {APP_DIR}")
logging.info(f"Script location: {os.path.abspath(__file__)}")

# Create output directories in the application directory
for dir_name in ["audio", "jsons", "edited", "subtitles"]:
    dir_path = os.path.join(APP_DIR, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    logging.info(f"Ensured output directory exists: {dir_path}")

# Try to import webrtcvad - if it fails, we'll try to install it
try:
    import webrtcvad

    logging.info("Successfully imported webrtcvad")
except ImportError:
    logging.warning("webrtcvad not found, attempting to install it")
    try:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "webrtcvad"])
        import webrtcvad

        logging.info("Successfully installed and imported webrtcvad")
    except Exception as e:
        logging.error(f"Failed to install webrtcvad: {e}")
        messagebox.showwarning(
            "Missing Dependency",
            "The 'webrtcvad' module could not be found or installed. Some functionality may not work correctly.",
        )

# Try to load environment variables
try:
    from dotenv import load_dotenv

    env_path = os.path.join(APP_DIR, ".env")
    load_dotenv(env_path)
    logging.info(f"Loaded .env file from {env_path}")
    # Log env variables for debugging (remove sensitive info in production)
    env_vars = {
        k: v
        for k, v in os.environ.items()
        if k.startswith("OPENAI_") and "KEY" not in k.upper()
    }
    logging.info(f"Environment variables: {env_vars}")
except Exception as e:
    logging.error(f"Error loading .env file: {e}")

# Import required modules directly to avoid dependency issues
try:
    # Import core dependencies
    from pydub import AudioSegment

    logging.info("Successfully imported pydub")

    # Import direct functions from source modules
    # These imports are explicit to ensure we have all required functions
    from src.audio.processing import detect_segments, extract_audio

    # Import the new UI components
    from src.gui.components import FolderButton, InfoIcon
    from src.gui.main_window import ModernVideoProcessorApp
    from src.gui.theme import ShadcnTheme
    from src.gui.tooltips import create_tooltip
    from src.llm.suggestion import get_llm_suggestion
    from src.transcription.whisper import transcribe_segments
    from src.utils.json_utils import load_json, save_json
    from src.utils.srt_utils import create_srt_from_json
    from src.video.editor import create_final_video

    logging.info("Successfully imported all required modules")

except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    messagebox.showerror(
        "Import Error",
        f"Failed to import required modules: {str(e)}. The application might not work correctly.",
    )


def main():
    """Application entry point"""
    try:
        logging.info("Starting main function")
        root = tk.Tk()
        app = ModernVideoProcessorApp(root, APP_DIR)
        logging.info("Entering Tkinter main loop")
        root.mainloop()
    except Exception as e:
        logging.critical(f"Fatal error in main function: {e}", exc_info=True)
        messagebox.showerror(
            "Fatal Error",
            f"A fatal error occurred: {str(e)}\n\nSee log file for details: {log_file}",
        )


if __name__ == "__main__":
    logging.info("Application entry point")
    main()
