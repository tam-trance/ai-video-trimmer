import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dotenv import load_dotenv

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
    from src.llm.suggestion import get_llm_suggestion
    from src.transcription.whisper import transcribe_segments
    from src.utils.json_utils import save_json
    from src.utils.srt_utils import create_srt_from_json
    from src.video.editor import create_final_video

    logging.info(
        "Successfully imported all required functions directly from source modules"
    )

    # Try importing process_video from main for completeness
    try:
        from main import process_video

        logging.info("Successfully imported process_video from main")
    except ImportError:
        logging.warning("Could not import process_video from main (this is optional)")

except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    messagebox.showerror(
        "Import Error",
        f"Failed to import required modules: {str(e)}. The application might not work correctly.",
    )


# Define the processing function locally to ensure it uses the imported functions
def process_video_local(video_path, generate_srt=True, generate_video=True):
    """Process a single video file using locally imported functions"""
    logging.info(f"Processing {video_path} using local implementation")
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Step 1: Extract full audio from the video
    temp_audio_file = os.path.join(APP_DIR, "audio", f"{base_name}_temp_audio.wav")
    extract_audio(video_path, temp_audio_file)

    # Load the audio as an AudioSegment for processing
    audio = AudioSegment.from_file(temp_audio_file)

    # Step 2: Detect segments
    segments = detect_segments(audio, chunk_ms=100)
    raw_segments_file = os.path.join(APP_DIR, "jsons", f"{base_name}_raw_segments.json")
    save_json(segments, raw_segments_file)
    logging.info(f"Saved raw segments JSON to {raw_segments_file}")

    # Step 3: Transcribe the segments
    raw_transcription = transcribe_segments(audio, segments)
    raw_transcription_file = os.path.join(
        APP_DIR, "jsons", f"{base_name}_transcription.json"
    )
    save_json(raw_transcription, raw_transcription_file)
    logging.info(f"Saved raw transcription JSON to {raw_transcription_file}")

    os.remove(temp_audio_file)

    # Step 4: Send raw transcription to an LLM for filtering and save suggestion JSON locally
    suggestion = get_llm_suggestion(raw_transcription)
    suggestion_file = os.path.join(APP_DIR, "jsons", f"{base_name}_suggestion.json")
    save_json(suggestion, suggestion_file)
    logging.info(f"Saved LLM suggestion JSON to {suggestion_file}")

    # Step 5: Create SRT file if requested
    if generate_srt:
        srt_content = create_srt_from_json(suggestion)
        srt_file = os.path.join(APP_DIR, "subtitles", f"{base_name}.srt")
        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)
        logging.info(f"Saved SRT file to {srt_file}")

    # Step 6: Create the final video if requested
    if generate_video:
        output_video = os.path.join(APP_DIR, "edited", f"{base_name}_edited.mp4")
        create_final_video(video_path, suggestion, output_video)
        logging.info(f"Saved edited video to {output_video}")

    return True


class VideoProcessorApp:
    def __init__(self, root):
        logging.info("Initializing VideoProcessorApp")
        self.root = root
        self.root.title("Video Processor")
        self.root.geometry("600x450")  # Made slightly taller for the buttons
        self.root.resizable(True, True)

        # Set application icon if it exists
        icon_path = os.path.join(APP_DIR, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                logging.warning(f"Could not set application icon: {e}")

        # Configure the grid layout
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=3)

        # Variables
        self.input_file = tk.StringVar()
        self.generate_srt = tk.BooleanVar(value=True)
        self.generate_video = tk.BooleanVar(value=True)
        self.processing = False
        self.current_progress = 0
        self.processing_steps = 6  # Total number of processing steps

        # Create the main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)

        # Input file selection
        ttk.Label(main_frame, text="Video File:").grid(
            row=0, column=0, sticky=tk.W, pady=10
        )
        input_entry = ttk.Entry(main_frame, textvariable=self.input_file)
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=10)
        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_input)
        browse_btn.grid(row=0, column=2, pady=10)

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Output Options", padding="10")
        options_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        # SRT option
        srt_check = ttk.Checkbutton(
            options_frame, text="Generate SRT subtitles", variable=self.generate_srt
        )
        srt_check.grid(row=0, column=0, sticky=tk.W, pady=5)

        # Video option
        video_check = ttk.Checkbutton(
            options_frame, text="Generate edited video", variable=self.generate_video
        )
        video_check.grid(row=1, column=0, sticky=tk.W, pady=5)

        # Output directory info
        output_frame = ttk.LabelFrame(main_frame, text="Output Location", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        output_label = ttk.Label(
            output_frame, text=f"All output files will be saved to:\n{APP_DIR}"
        )
        output_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        # Progress indicators
        self.progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        self.progress_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )

        self.progress_label = ttk.Label(
            self.progress_frame, text="Ready to process video"
        )
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.progress_bar = ttk.Progressbar(
            self.progress_frame, orient=tk.HORIZONTAL, length=100, mode="determinate"
        )
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=10)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)

        # Process button
        self.process_btn = ttk.Button(
            buttons_frame, text="Process Video", command=self.start_processing
        )
        self.process_btn.grid(row=0, column=0, pady=5, padx=10)

        # Open Output Folder button
        self.open_folder_btn = ttk.Button(
            buttons_frame, text="Open Output Folder", command=self.open_output_folder
        )
        self.open_folder_btn.grid(row=0, column=1, pady=5, padx=10)

        # Log entry
        self.log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        self.log_frame.grid(
            row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )
        self.log_frame.rowconfigure(0, weight=1)
        self.log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(self.log_frame, height=5, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_text.insert(tk.END, f"Log file: {log_file}\n")
        self.log_text.config(state=tk.DISABLED)

        # Add scrollbar to log text
        scrollbar = ttk.Scrollbar(
            self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)

        logging.info("GUI setup complete")
        self.log_message("Application initialized successfully")

    def log_message(self, message):
        logging.info(message)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def browse_input(self):
        self.log_message("Browsing for input video file...")
        file_types = [("Video files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")]
        file_path = filedialog.askopenfilename(
            title="Select Video File", filetypes=file_types
        )
        if file_path:
            self.input_file.set(file_path)
            self.log_message(f"Selected video file: {file_path}")

    def open_output_folder(self):
        """Open the output folder in file explorer"""
        try:
            if self.generate_video.get():
                folder_path = os.path.join(APP_DIR, "edited")
            elif self.generate_srt.get():
                folder_path = os.path.join(APP_DIR, "subtitles")
            else:
                folder_path = os.path.join(APP_DIR, "jsons")

            # Ensure the folder exists
            os.makedirs(folder_path, exist_ok=True)

            # Open the folder using the system's file explorer
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])

            self.log_message(f"Opened output folder: {folder_path}")
        except Exception as e:
            self.log_message(f"Error opening output folder: {str(e)}")

    def update_progress(self, step, message):
        """Update the progress bar and label"""
        progress_value = int((step / self.processing_steps) * 100)
        self.root.after(0, lambda: self.progress_bar.config(value=progress_value))
        self.root.after(0, lambda: self.progress_label.config(text=message))
        self.log_message(message)

    def start_processing(self):
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select a video file")
            return

        if self.processing:
            return

        video_path = self.input_file.get()
        if not os.path.isfile(video_path):
            messagebox.showerror("Error", f"Video file not found: {video_path}")
            return

        # Start processing in a separate thread
        self.processing = True
        self.log_message("Starting video processing...")
        self.progress_label.config(text="Processing video... Please wait")
        self.progress_bar.config(value=0)  # Reset progress bar
        self.process_btn.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.run_process_video)
        thread.daemon = True
        thread.start()

    def run_process_video(self):
        """Execute the video processing function with progress updates"""
        try:
            video_path = self.input_file.get()
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_video = os.path.join(APP_DIR, "edited", f"{base_name}_edited.mp4")

            # Use the locally defined functions directly to avoid any import issues
            try:
                # Step 1: Extract audio
                temp_audio_file = os.path.join(
                    APP_DIR, "audio", f"{base_name}_temp_audio.wav"
                )
                self.update_progress(1, f"Extracting audio to {temp_audio_file}...")
                extract_audio(video_path, temp_audio_file)

                # Load the audio file as AudioSegment for further processing
                self.update_progress(1.5, "Loading audio file...")
                audio = AudioSegment.from_file(temp_audio_file)

                # Step 2: Detect segments with chunk_ms parameter to match main.py exactly
                self.update_progress(2, "Detecting speech segments...")
                segments = detect_segments(audio, chunk_ms=100)
                raw_segments_file = os.path.join(
                    APP_DIR, "jsons", f"{base_name}_raw_segments.json"
                )
                save_json(segments, raw_segments_file)

                # Step 3: Transcribe segments
                self.update_progress(3, "Transcribing audio segments...")
                raw_transcription = transcribe_segments(audio, segments)
                raw_transcription_file = os.path.join(
                    APP_DIR, "jsons", f"{base_name}_transcription.json"
                )
                save_json(raw_transcription, raw_transcription_file)

                # Clean up temp audio file
                os.remove(temp_audio_file)

                # Step 4: Get LLM suggestions
                self.update_progress(4, "Processing transcription with LLM...")
                suggestion = get_llm_suggestion(raw_transcription)
                suggestion_file = os.path.join(
                    APP_DIR, "jsons", f"{base_name}_suggestion.json"
                )
                save_json(suggestion, suggestion_file)

                # Step 5: Create SRT if requested
                if self.generate_srt.get():
                    self.update_progress(5, "Generating SRT subtitles...")
                    srt_content = create_srt_from_json(suggestion)
                    srt_file = os.path.join(APP_DIR, "subtitles", f"{base_name}.srt")
                    with open(srt_file, "w", encoding="utf-8") as f:
                        f.write(srt_content)
                else:
                    self.update_progress(5, "Skipping SRT generation...")

                # Step 6: Create final video if requested
                if self.generate_video.get():
                    self.update_progress(6, "Creating edited video...")
                    create_final_video(video_path, suggestion, output_video)
                else:
                    self.update_progress(6, "Skipping video generation...")

                self.update_progress(
                    self.processing_steps,
                    f"Finished processing: {os.path.basename(video_path)}",
                )

                # Show success message with output paths
                success_message = (
                    f"Successfully processed {os.path.basename(video_path)}!\n\n"
                )

                if self.generate_srt.get():
                    srt_path = os.path.join(APP_DIR, "subtitles", f"{base_name}.srt")
                    success_message += f"SRT file: {srt_path}\n"

                if self.generate_video.get():
                    success_message += f"Edited video: {output_video}\n"

                self.root.after(
                    0, lambda: messagebox.showinfo("Success", success_message)
                )

            except Exception as e:
                error_msg = f"Error processing {os.path.basename(video_path)}: {str(e)}"
                self.log_message(error_msg)
                logging.error(error_msg, exc_info=True)
                self.root.after(
                    0,
                    lambda err=error_msg: messagebox.showerror("Processing Error", err),
                )

            self.finish_processing("Processing complete")

        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            self.log_message(error_msg)
            logging.error(error_msg, exc_info=True)
            self.root.after(
                0,
                lambda err=error_msg: messagebox.showerror("Error", err),
            )
            self.finish_processing(f"Error: {str(e)}")

    def finish_processing(self, message):
        self.progress_bar.config(value=100)  # Complete the progress bar
        self.progress_label.config(text=message)
        self.process_btn.config(state=tk.NORMAL)
        self.processing = False
        self.log_message(message)


def main():
    try:
        logging.info("Starting main function")
        root = tk.Tk()
        app = VideoProcessorApp(root)
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
