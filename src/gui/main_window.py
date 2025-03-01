"""
Main Window for Video Processing Application

This module provides a modern UI for the video processor with step-by-step buttons
and parameter controls.
"""

import logging
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from src.gui.components import FolderButton, InfoIcon
from src.gui.processing_controller import ProcessingController
from src.gui.theme import ShadcnTheme
from src.gui.tooltips import create_tooltip


class ModernVideoProcessorApp:
    """
    Modern UI for the Video Processor Application with step-by-step processing
    """

    def __init__(self, root, app_dir):
        """
        Initialize the application UI

        Args:
            root: Tkinter root window
            app_dir: Application directory
        """
        self.root = root
        self.app_dir = app_dir
        self.controller = ProcessingController(app_dir)

        # Set up the window
        self.setup_window()

        # Apply the modern theme
        self.theme = ShadcnTheme(root)

        # Create UI components
        self.create_main_frame()
        self.create_header()
        self.create_two_column_layout()

        # Processing variables
        self.processing_thread = None
        self.processing = False

        logging.info("Modern UI initialized")

    def setup_window(self):
        """Set up the main window properties"""
        self.root.title("Video Processor")
        self.root.geometry("1280x720")  # Wider window to accommodate horizontal layout
        self.root.minsize(1024, 600)  # Increased minimum width

        # Set icon if available
        icon_path = os.path.join(self.app_dir, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                logging.warning(f"Could not set application icon: {e}")

        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def create_main_frame(self):
        """Create the main application frame"""
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure main frame grid
        self.main_frame.columnconfigure(0, weight=3)  # Left column (main workflow)
        self.main_frame.columnconfigure(1, weight=1)  # Right column (output files)
        self.main_frame.rowconfigure(1, weight=1)  # Content row should expand

    def create_header(self):
        """Create the application header"""
        header = ttk.Label(
            self.main_frame, text="Video Processor", style="Header.TLabel"
        )
        header.grid(row=0, column=0, columnspan=2, sticky="nw", pady=(0, 15))

    def create_two_column_layout(self):
        """Create the two-column layout with processing on left, output on right"""
        # Left column container for main workflow
        self.left_column = ttk.Frame(self.main_frame)
        self.left_column.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.left_column.columnconfigure(0, weight=1)
        self.left_column.rowconfigure(2, weight=1)  # Make log section expandable

        # Right column for log only (removed output files section)
        self.right_column = ttk.Frame(self.main_frame)
        self.right_column.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.right_column.columnconfigure(0, weight=1)
        self.right_column.rowconfigure(0, weight=1)  # Make log section take full height

        # Create sections in the left column
        self.create_upper_section()
        self.create_processing_section()

        # Create the log section directly in the right column
        self.create_log_section()

    def create_upper_section(self):
        """Create the upper section containing file selection and parameters side by side"""
        upper_frame = ttk.Frame(self.left_column)
        upper_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        upper_frame.columnconfigure(0, weight=1)
        upper_frame.columnconfigure(1, weight=1)

        # File selection section (left side)
        self.create_file_section(upper_frame, 0)

        # Parameters section (right side)
        self.create_parameters_section(upper_frame, 1)

    def create_file_section(self, parent, column):
        """Create the file selection section"""
        file_frame = ttk.LabelFrame(parent, text="Video Selection", padding="10")
        file_frame.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 10, 10 if column == 0 else 0),
        )
        file_frame.columnconfigure(1, weight=1)

        # File selection
        ttk.Label(file_frame, text="Video File:").grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.input_file = tk.StringVar()
        input_entry = ttk.Entry(file_frame, textvariable=self.input_file)
        input_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        browse_btn = ttk.Button(
            file_frame,
            text="Browse",
            command=self.browse_input,
            style="Primary.TButton",
            width=8,
        )
        browse_btn.grid(row=0, column=2, pady=5, padx=(0, 5))

        # Open videos folder button
        videos_folder_btn = FolderButton(
            file_frame,
            os.path.dirname(self.app_dir) if self.app_dir else os.path.expanduser("~"),
            tooltip_text="Open videos folder",
        )
        videos_folder_btn.grid(row=0, column=3, pady=5, padx=(0, 5))

        # File status
        self.file_status = ttk.Label(
            file_frame, text="No file selected", style="Status.TLabel"
        )
        self.file_status.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 5))

    def create_parameters_section(self, parent, column):
        """Create the segment detection parameters section"""
        params_frame = ttk.LabelFrame(
            parent, text="Segment Detection Parameters", padding="10"
        )
        params_frame.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(10 if column == 0 else 0, 0 if column == 0 else 10),
        )

        # Create a 2x2 grid for parameters
        for i in range(2):
            params_frame.columnconfigure(i * 3, weight=0)  # Label column
            params_frame.columnconfigure(i * 3 + 1, weight=0)  # Value column
            params_frame.columnconfigure(i * 3 + 2, weight=1)  # Info column

        # Frame Duration parameter
        ttk.Label(params_frame, text="Frame Duration (ms):").grid(
            row=0, column=0, sticky="w", pady=5, padx=(0, 5)
        )

        self.frame_duration = tk.IntVar(value=30)
        frame_values = [10, 20, 30]  # Only these values are supported
        frame_combo = ttk.Combobox(
            params_frame,
            textvariable=self.frame_duration,
            values=frame_values,
            state="readonly",
            width=5,
        )
        frame_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Use the InfoIcon component instead of ttk.Label
        frame_info = InfoIcon(
            params_frame,
            "Frame duration in milliseconds. WebRTC VAD only supports 10, 20, or 30ms. "
            "Shorter frames provide more precise segmentation but may be more sensitive to noise.",
        )
        frame_info.grid(row=0, column=2, sticky="w", padx=(5, 20))

        # Padding Duration parameter
        ttk.Label(params_frame, text="Padding Duration (ms):").grid(
            row=0, column=3, sticky="w", pady=5, padx=(20, 5)
        )

        self.padding_duration = tk.IntVar(value=300)
        padding_spinbox = ttk.Spinbox(
            params_frame,
            from_=50,
            to=1000,
            increment=50,
            textvariable=self.padding_duration,
            width=5,
        )
        padding_spinbox.grid(row=0, column=4, sticky="w", pady=5)

        # Use the InfoIcon component
        padding_info = InfoIcon(
            params_frame,
            "Maximum gap between speech segments (in ms) to consider them as a single segment. "
            "Higher values merge segments that are close together, reducing the number of cuts.",
        )
        padding_info.grid(row=0, column=5, sticky="w", padx=(5, 10))

        # Aggressiveness parameter
        ttk.Label(params_frame, text="Aggressiveness (0-3):").grid(
            row=1, column=0, sticky="w", pady=5, padx=(0, 5)
        )

        self.aggressiveness = tk.IntVar(value=3)
        agg_values = [0, 1, 2, 3]
        agg_combo = ttk.Combobox(
            params_frame,
            textvariable=self.aggressiveness,
            values=agg_values,
            state="readonly",
            width=5,
        )
        agg_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Use the InfoIcon component
        agg_info = InfoIcon(
            params_frame,
            "VAD aggressiveness (0-3). Higher values are more aggressive in filtering out non-speech. "
            "0 is least aggressive, 3 is most aggressive in labeling audio as speech.",
        )
        agg_info.grid(row=1, column=2, sticky="w", padx=(5, 20))

        # Post-speech padding parameter
        ttk.Label(params_frame, text="Post-speech Padding (sec):").grid(
            row=1, column=3, sticky="w", pady=5, padx=(20, 5)
        )

        self.post_padding = tk.DoubleVar(value=0.2)
        post_spinbox = ttk.Spinbox(
            params_frame,
            from_=0.0,
            to=1.0,
            increment=0.1,
            textvariable=self.post_padding,
            width=5,
        )
        post_spinbox.grid(row=1, column=4, sticky="w", pady=5)

        # Use the InfoIcon component
        post_info = InfoIcon(
            params_frame,
            "Additional padding (in seconds) to add after each speech segment. "
            "Higher values include more audio after speech ends, preventing cutoffs.",
        )
        post_info.grid(row=1, column=5, sticky="w", padx=(5, 10))

        # Apply parameters button - Higher contrast with Primary style
        self.apply_params_btn = ttk.Button(
            params_frame,
            text="Apply Parameters",
            command=self.apply_parameters,
            style="Primary.TButton",  # Changed to Primary for better contrast
            width=16,
        )
        self.apply_params_btn.grid(row=2, column=0, columnspan=6, pady=(8, 0))

    def create_processing_section(self):
        """Create the step-by-step processing section"""
        process_frame = ttk.LabelFrame(
            self.left_column, text="Processing Steps", padding="10"
        )
        process_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Configure grid for 3-column layout
        for i in range(3):
            process_frame.columnconfigure(i, weight=1)

        # Step 1: Raw Segments
        step1_frame = ttk.Frame(process_frame)
        step1_frame.grid(row=0, column=0, sticky="ew", padx=5)
        step1_frame.columnconfigure(0, weight=1)

        self.step1_btn = ttk.Button(
            step1_frame,
            text="1. Detect Speech Segments",
            style="Processing.TButton",
            command=self.run_detect_segments,
        )
        self.step1_btn.grid(row=0, column=0, pady=5, sticky="ew")

        step1_status_frame = ttk.Frame(step1_frame)
        step1_status_frame.grid(row=1, column=0, sticky="ew")
        step1_status_frame.columnconfigure(0, weight=1)

        self.step1_status = ttk.Label(
            step1_status_frame, text="Not started", style="Status.TLabel"
        )
        self.step1_status.grid(row=0, column=0, sticky="w", pady=5)

        # Add folder button for segments
        self.segments_folder_btn = FolderButton(
            step1_status_frame,
            self.controller.dirs["jsons"],
            tooltip_text="Open segments folder",
        )
        self.segments_folder_btn.grid(row=0, column=1, pady=5, padx=5)

        # Step 2: Transcription
        step2_frame = ttk.Frame(process_frame)
        step2_frame.grid(row=0, column=1, sticky="ew", padx=5)
        step2_frame.columnconfigure(0, weight=1)

        self.step2_btn = ttk.Button(
            step2_frame,
            text="2. Transcribe Segments",
            style="Processing.TButton",
            command=self.run_transcribe_segments,
            state="disabled",
        )
        self.step2_btn.grid(row=0, column=0, pady=5, sticky="ew")

        step2_status_frame = ttk.Frame(step2_frame)
        step2_status_frame.grid(row=1, column=0, sticky="ew")
        step2_status_frame.columnconfigure(0, weight=1)

        self.step2_status = ttk.Label(
            step2_status_frame,
            text="Waiting for segment detection",
            style="Status.TLabel",
        )
        self.step2_status.grid(row=0, column=0, sticky="w", pady=5)

        # Add folder button for transcription
        self.transcription_folder_btn = FolderButton(
            step2_status_frame,
            self.controller.dirs["jsons"],
            tooltip_text="Open transcriptions folder",
        )
        self.transcription_folder_btn.grid(row=0, column=1, pady=5, padx=5)

        # Step 3: LLM Suggestions
        step3_frame = ttk.Frame(process_frame)
        step3_frame.grid(row=0, column=2, sticky="ew", padx=5)
        step3_frame.columnconfigure(0, weight=1)

        self.step3_btn = ttk.Button(
            step3_frame,
            text="3. Generate LLM Suggestions",
            style="Processing.TButton",
            command=self.run_generate_suggestions,
            state="disabled",
        )
        self.step3_btn.grid(row=0, column=0, pady=5, sticky="ew")

        step3_status_frame = ttk.Frame(step3_frame)
        step3_status_frame.grid(row=1, column=0, sticky="ew")
        step3_status_frame.columnconfigure(0, weight=1)

        self.step3_status = ttk.Label(
            step3_status_frame, text="Waiting for transcription", style="Status.TLabel"
        )
        self.step3_status.grid(row=0, column=0, sticky="w", pady=5)

        # Add folder button for suggestions
        self.suggestions_folder_btn = FolderButton(
            step3_status_frame,
            self.controller.dirs["jsons"],
            tooltip_text="Open suggestions folder",
        )
        self.suggestions_folder_btn.grid(row=0, column=1, pady=5, padx=5)

        # Output options in a separate row
        output_frame = ttk.Frame(process_frame)
        output_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.columnconfigure(1, weight=1)

        # SRT Generation
        self.generate_srt = tk.BooleanVar(value=True)
        self.srt_frame = ttk.Frame(output_frame)
        self.srt_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.srt_frame.columnconfigure(0, weight=1)

        self.srt_btn = ttk.Button(
            self.srt_frame,
            text="4a. Generate SRT",
            style="Processing.TButton",
            command=self.run_generate_srt,
            state="disabled",
        )
        self.srt_btn.grid(row=0, column=0, pady=5, sticky="ew")

        srt_status_frame = ttk.Frame(self.srt_frame)
        srt_status_frame.grid(row=1, column=0, sticky="ew")
        srt_status_frame.columnconfigure(0, weight=1)

        self.srt_status = ttk.Label(
            srt_status_frame, text="Waiting for suggestions", style="Status.TLabel"
        )
        self.srt_status.grid(row=0, column=0, sticky="w", pady=5)

        # Add folder button for SRT
        self.srt_folder_btn = FolderButton(
            srt_status_frame,
            self.controller.dirs["subtitles"],
            tooltip_text="Open subtitles folder",
        )
        self.srt_folder_btn.grid(row=0, column=1, pady=5, padx=5)

        # Video Generation
        self.generate_video = tk.BooleanVar(value=True)
        self.video_frame = ttk.Frame(output_frame)
        self.video_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.video_frame.columnconfigure(0, weight=1)

        self.video_btn = ttk.Button(
            self.video_frame,
            text="4b. Generate Video",
            style="Processing.TButton",
            command=self.run_generate_video,
            state="disabled",
        )
        self.video_btn.grid(row=0, column=0, pady=5, sticky="ew")

        video_status_frame = ttk.Frame(self.video_frame)
        video_status_frame.grid(row=1, column=0, sticky="ew")
        video_status_frame.columnconfigure(0, weight=1)

        self.video_status = ttk.Label(
            video_status_frame, text="Waiting for suggestions", style="Status.TLabel"
        )
        self.video_status.grid(row=0, column=0, sticky="w", pady=5)

        # Add folder button for edited videos
        self.edited_folder_btn = FolderButton(
            video_status_frame,
            self.controller.dirs["edited"],
            tooltip_text="Open edited videos folder",
        )
        self.edited_folder_btn.grid(row=0, column=1, pady=5, padx=5)

    def create_log_section(self):
        """Create the log section in the right column"""
        log_frame = ttk.LabelFrame(self.right_column, text="Log", padding="10")
        log_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        # Log text widget
        self.log_text = tk.Text(
            log_frame,
            height=12,
            wrap=tk.WORD,
            background=self.theme.get_color("surface"),
            foreground=self.theme.get_color("foreground"),
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10,
            font=self.theme.get_font("default"),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.config(state=tk.DISABLED)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            log_frame, orient=tk.VERTICAL, command=self.log_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # Log initial message
        self.log_message("Application initialized successfully")

    def log_message(self, message):
        """Log a message to the log widget and logger

        Args:
            message: Message to log
        """
        logging.info(message)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def browse_input(self):
        """Browse for input video file"""
        self.log_message("Browsing for input video file...")
        file_types = [("Video files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")]
        file_path = filedialog.askopenfilename(
            title="Select Video File", filetypes=file_types
        )

        if file_path:
            self.input_file.set(file_path)
            self.controller.set_video_path(file_path)
            self.file_status.config(
                text=f"Selected: {os.path.basename(file_path)}", style="Success.TLabel"
            )
            self.log_message(f"Selected video file: {file_path}")

            # Check for existing JSON files
            self.check_existing_files()

            # Update button states
            self.update_button_states()

    def check_existing_files(self):
        """Check if JSON files already exist for the selected video and update UI accordingly"""
        if not self.controller.video_path:
            return

        # Check dependencies using the controller
        deps = self.controller.check_dependencies()

        # Update UI based on what files exist
        if deps["segments_detected"]:
            self.step1_status.config(
                text=f"Found: {os.path.basename(self.controller.segments_file)}",
                style="Success.TLabel",
            )
            self.step2_btn.config(state=tk.NORMAL)
            self.log_message(
                f"Found existing segments file: {self.controller.segments_file}"
            )

        if deps["transcription_complete"]:
            self.step2_status.config(
                text=f"Found: {os.path.basename(self.controller.transcription_file)}",
                style="Success.TLabel",
            )
            self.step3_btn.config(state=tk.NORMAL)
            self.log_message(
                f"Found existing transcription file: {self.controller.transcription_file}"
            )

        if deps["suggestion_complete"]:
            self.step3_status.config(
                text=f"Found: {os.path.basename(self.controller.suggestion_file)}",
                style="Success.TLabel",
            )
            self.srt_btn.config(state=tk.NORMAL)
            self.video_btn.config(state=tk.NORMAL)
            self.srt_status.config(text="Ready", style="Status.TLabel")
            self.video_status.config(text="Ready", style="Status.TLabel")
            self.log_message(
                f"Found existing suggestion file: {self.controller.suggestion_file}"
            )

        if deps["srt_generated"]:
            self.srt_status.config(
                text=f"Found: {os.path.basename(self.controller.srt_file)}",
                style="Success.TLabel",
            )
            self.log_message(f"Found existing SRT file: {self.controller.srt_file}")

        if deps["video_generated"]:
            self.video_status.config(
                text=f"Found: {os.path.basename(self.controller.output_video)}",
                style="Success.TLabel",
            )
            self.log_message(
                f"Found existing edited video: {self.controller.output_video}"
            )

    def apply_parameters(self):
        """Apply the segment detection parameters"""
        if not self.controller.video_path:
            messagebox.showwarning(
                "No Video Selected", "Please select a video file first."
            )
            return

        # Apply parameters
        self.controller.frame_duration = self.frame_duration.get()
        self.controller.padding_duration = self.padding_duration.get()
        self.controller.aggressiveness = self.aggressiveness.get()
        self.controller.post_padding = self.post_padding.get()

        # Log the applied parameters
        self.log_message(
            f"Applied parameters: frame_duration={self.frame_duration.get()}ms, "
            f"padding_duration={self.padding_duration.get()}ms, "
            f"aggressiveness={self.aggressiveness.get()}, "
            f"post_padding={self.post_padding.get()}s"
        )

    def update_button_states(self):
        """Update the enabled/disabled state of the processing buttons"""
        # Enable step 1 if video is selected
        if self.controller.video_path:
            self.step1_btn.config(state=tk.NORMAL)
        else:
            self.step1_btn.config(state=tk.DISABLED)
            self.step2_btn.config(state=tk.DISABLED)
            self.step3_btn.config(state=tk.DISABLED)
            self.srt_btn.config(state=tk.DISABLED)
            self.video_btn.config(state=tk.DISABLED)

    def run_detect_segments(self):
        """Run step 1: Detect speech segments"""
        if not self.controller.video_path:
            messagebox.showwarning(
                "No Video Selected", "Please select a video file first."
            )
            return

        # Update parameters
        self.controller.update_segment_params(
            frame_duration_ms=self.frame_duration.get(),
            padding_duration_ms=self.padding_duration.get(),
            aggressiveness=self.aggressiveness.get(),
            post_speech_padding_sec=self.post_padding.get(),
        )

        # Disable UI during processing
        self.step1_btn.config(state=tk.DISABLED)
        self.step1_status.config(text="Processing...", style="Info.TLabel")
        self.processing = True

        # Start processing in a separate thread
        def process_task():
            try:
                self.log_message("Starting speech segment detection...")

                # Run the processing with progress updates
                def update_progress(msg):
                    self.log_message(msg)

                segments_file = self.controller.process_raw_segments(
                    progress_callback=update_progress
                )

                # Update UI on completion
                self.root.after(0, lambda: self._on_segments_complete(segments_file))
            except Exception as e:
                # Handle errors
                error_msg = f"Error during segment detection: {str(e)}"
                self.root.after(0, lambda: self._on_processing_error(error_msg))

        # Start processing thread
        self.processing_thread = threading.Thread(target=process_task)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _on_segments_complete(self, segments_file):
        """Called when segment detection is complete"""
        self.processing = False

        if segments_file and os.path.exists(segments_file):
            self.step1_status.config(
                text=f"Completed: {os.path.basename(segments_file)}",
                style="Success.TLabel",
            )
            self.log_message(
                f"Segment detection completed successfully: {segments_file}"
            )

            # Enable the next step
            self.step2_btn.config(state=tk.NORMAL)
            self.step2_status.config(text="Ready", style="Status.TLabel")
        else:
            self.step1_status.config(
                text="Failed to detect segments", style="Error.TLabel"
            )
            self.log_message("Segment detection failed - no output file generated")

        # Re-enable the button
        self.step1_btn.config(state=tk.NORMAL)

    def run_transcribe_segments(self):
        """Run step 2: Transcribe segments"""
        # Check dependencies
        deps = self.controller.check_dependencies()
        if not deps["segments_detected"]:
            messagebox.showwarning(
                "No Segments Detected", "Please detect segments first."
            )
            return

        # Disable UI during processing
        self.step2_btn.config(state=tk.DISABLED)
        self.step2_status.config(text="Processing...", style="Info.TLabel")
        self.processing = True

        # Start processing in a separate thread
        def process_task():
            try:
                self.log_message("Starting transcription of speech segments...")

                # Run the processing with progress updates
                def update_progress(msg):
                    self.log_message(msg)

                transcription_file = self.controller.process_transcription(
                    progress_callback=update_progress
                )

                # Update UI on completion
                self.root.after(
                    0, lambda: self._on_transcription_complete(transcription_file)
                )
            except Exception as e:
                # Handle errors
                error_msg = f"Error during transcription: {str(e)}"
                self.root.after(0, lambda: self._on_processing_error(error_msg))

        # Start processing thread
        self.processing_thread = threading.Thread(target=process_task)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _on_transcription_complete(self, transcription_file):
        """Called when transcription is complete"""
        self.processing = False

        if transcription_file and os.path.exists(transcription_file):
            self.step2_status.config(
                text=f"Completed: {os.path.basename(transcription_file)}",
                style="Success.TLabel",
            )
            self.log_message(
                f"Transcription completed successfully: {transcription_file}"
            )

            # Enable the next step
            self.step3_btn.config(state=tk.NORMAL)
            self.step3_status.config(text="Ready", style="Status.TLabel")
        else:
            self.step2_status.config(
                text="Failed to transcribe segments", style="Error.TLabel"
            )
            self.log_message("Transcription failed - no output file generated")

        # Re-enable the button
        self.step2_btn.config(state=tk.NORMAL)

    def run_generate_suggestions(self):
        """Run step 3: Generate LLM suggestions"""
        # Check dependencies
        deps = self.controller.check_dependencies()
        if not deps["transcription_complete"]:
            messagebox.showwarning(
                "No Transcription Available", "Please transcribe segments first."
            )
            return

        # Disable UI during processing
        self.step3_btn.config(state=tk.DISABLED)
        self.step3_status.config(text="Processing...", style="Info.TLabel")
        self.processing = True

        # Start processing in a separate thread
        def process_task():
            try:
                self.log_message("Starting LLM suggestion generation...")

                # Run the processing with progress updates
                def update_progress(msg):
                    self.log_message(msg)

                suggestion_file = self.controller.process_suggestions(
                    progress_callback=update_progress
                )

                # Update UI on completion
                self.root.after(
                    0, lambda: self._on_suggestions_complete(suggestion_file)
                )
            except Exception as e:
                # Handle errors
                error_msg = f"Error during suggestion generation: {str(e)}"
                self.root.after(0, lambda: self._on_processing_error(error_msg))

        # Start processing thread
        self.processing_thread = threading.Thread(target=process_task)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _on_suggestions_complete(self, suggestion_file):
        """Called when suggestion generation is complete"""
        self.processing = False

        if suggestion_file and os.path.exists(suggestion_file):
            self.step3_status.config(
                text=f"Completed: {os.path.basename(suggestion_file)}",
                style="Success.TLabel",
            )
            self.log_message(
                f"Suggestion generation completed successfully: {suggestion_file}"
            )

            # Enable the output steps
            self.srt_btn.config(state=tk.NORMAL)
            self.srt_status.config(text="Ready", style="Status.TLabel")
            self.video_btn.config(state=tk.NORMAL)
            self.video_status.config(text="Ready", style="Status.TLabel")
        else:
            self.step3_status.config(
                text="Failed to generate suggestions", style="Error.TLabel"
            )
            self.log_message("Suggestion generation failed - no output file generated")

        # Re-enable the button
        self.step3_btn.config(state=tk.NORMAL)

    def run_generate_srt(self):
        """Run step 4a: Generate SRT file"""
        # Check dependencies
        deps = self.controller.check_dependencies()
        if not deps["suggestion_complete"]:
            messagebox.showwarning(
                "No Suggestions Available", "Please generate suggestions first."
            )
            return

        # Disable UI during processing
        self.srt_btn.config(state=tk.DISABLED)
        self.srt_status.config(text="Processing...", style="Info.TLabel")
        self.processing = True

        # Start processing in a separate thread
        def process_task():
            try:
                self.log_message("Starting SRT subtitle generation...")

                # Run the processing with progress updates
                def update_progress(msg):
                    self.log_message(msg)

                srt_file = self.controller.generate_srt(
                    progress_callback=update_progress
                )

                # Update UI on completion
                self.root.after(0, lambda: self._on_srt_complete(srt_file))
            except Exception as e:
                # Handle errors
                error_msg = f"Error during SRT generation: {str(e)}"
                self.root.after(0, lambda: self._on_processing_error(error_msg))

        # Start processing thread
        self.processing_thread = threading.Thread(target=process_task)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _on_srt_complete(self, srt_file):
        """Called when SRT generation is complete"""
        self.processing = False

        if srt_file and os.path.exists(srt_file):
            self.srt_status.config(
                text=f"Completed: {os.path.basename(srt_file)}", style="Success.TLabel"
            )
            self.log_message(f"SRT generation completed successfully: {srt_file}")
        else:
            self.srt_status.config(text="Failed to generate SRT", style="Error.TLabel")
            self.log_message("SRT generation failed - no output file generated")

        # Re-enable the button
        self.srt_btn.config(state=tk.NORMAL)

    def run_generate_video(self):
        """Run step 4b: Generate edited video"""
        # Check dependencies
        deps = self.controller.check_dependencies()
        if not deps["suggestion_complete"]:
            messagebox.showwarning(
                "No Suggestions Available", "Please generate suggestions first."
            )
            return

        # Disable UI during processing
        self.video_btn.config(state=tk.DISABLED)
        self.video_status.config(text="Processing...", style="Info.TLabel")
        self.processing = True

        # Start processing in a separate thread
        def process_task():
            try:
                self.log_message("Starting edited video generation...")

                # Run the processing with progress updates
                def update_progress(msg):
                    self.log_message(msg)

                video_file = self.controller.generate_edited_video(
                    progress_callback=update_progress
                )

                # Update UI on completion
                self.root.after(0, lambda: self._on_video_complete(video_file))
            except Exception as e:
                # Handle errors
                error_msg = f"Error during video generation: {str(e)}"
                self.root.after(0, lambda: self._on_processing_error(error_msg))

        # Start processing thread
        self.processing_thread = threading.Thread(target=process_task)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _on_video_complete(self, video_file):
        """Called when video generation is complete"""
        self.processing = False

        if video_file and os.path.exists(video_file):
            self.video_status.config(
                text=f"Completed: {os.path.basename(video_file)}",
                style="Success.TLabel",
            )
            self.log_message(
                f"Edited video generation completed successfully: {video_file}"
            )
        else:
            self.video_status.config(
                text="Failed to generate video", style="Error.TLabel"
            )
            self.log_message("Video generation failed - no output file generated")

        # Re-enable the button
        self.video_btn.config(state=tk.NORMAL)

    def _on_processing_error(self, error_msg):
        """Handle processing errors"""
        self.processing = False
        logging.error(error_msg)
        self.log_message(error_msg)

        # Ensure all buttons are enabled
        self.step1_btn.config(state=tk.NORMAL)
        if hasattr(self, "step2_btn"):
            self.step2_btn.config(state=tk.NORMAL)
        if hasattr(self, "step3_btn"):
            self.step3_btn.config(state=tk.NORMAL)
        if hasattr(self, "srt_btn"):
            self.srt_btn.config(state=tk.NORMAL)
        if hasattr(self, "video_btn"):
            self.video_btn.config(state=tk.NORMAL)

        # Show error message
        messagebox.showerror("Processing Error", error_msg)
