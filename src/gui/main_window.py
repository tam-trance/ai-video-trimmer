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

from src.gui import theme
from src.gui.components import FolderButton, InfoIcon
from src.gui.processing_controller import ProcessingController
from src.gui.tooltips import create_tooltip


class ModernVideoProcessorApp:
    """
    Modern UI for the Video Processor Application with step-by-step processing
    """

    def __init__(self, root, app_dir=None):
        """Initialize the main application window"""
        self.root = root
        root.title("AI Video Trimmer")

        self.app_dir = app_dir or os.path.dirname(os.path.abspath(__file__))
        self.controller = ProcessingController(self.app_dir)
        self.controller.set_callback(self.update_log)

        # Initialize file tracking
        self.current_file = None

        # Configure the theme
        self.theme = theme.setup_theme(root)

        # Set geometry and minimum size
        root.geometry("1200x700")
        root.minsize(1000, 600)

        # Configure main grid
        self.configure_grid()

        # Create the two-column layout
        self.create_two_column_layout()

        # Processing variables
        self.processing_thread = None
        self.processing = False

        logging.info("Modern UI initialized")

    def configure_grid(self):
        """Configure the main grid layout"""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def create_two_column_layout(self):
        """Create the two-column layout with processing on left, output on right"""
        # Left column container for main workflow
        self.left_column = ttk.Frame(self.root)
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_column.columnconfigure(0, weight=1)
        self.left_column.rowconfigure(2, weight=1)  # Make log section expandable

        # Right column for log only (removed output files section)
        self.right_column = ttk.Frame(self.root)
        self.right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.right_column.columnconfigure(0, weight=1)
        self.right_column.rowconfigure(0, weight=1)  # Make log section take full height

        # Create sections in the left column
        self.create_upper_section()
        self.create_processing_section()

        # Create the log section directly in the right column
        self.create_log_section()

    def create_upper_section(self):
        """Create the upper section containing file selection and parameters side by side"""
        self.upper_frame = ttk.Frame(self.left_column)
        self.upper_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.upper_frame.columnconfigure(0, weight=1)
        self.upper_frame.columnconfigure(1, weight=1)

        # File selection section (left side)
        self.create_file_section()

        # Parameters section (right side)
        self.create_parameters_section()

    def create_file_section(self):
        """Create the file selection section"""
        file_frame = ttk.LabelFrame(
            self.upper_frame, text="File Selection", padding="10"
        )
        file_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        file_frame.columnconfigure(0, weight=1)
        file_frame.columnconfigure(1, weight=0)
        file_frame.columnconfigure(2, weight=0)

        # Row 0: Title and Browse buttons
        self.file_label = ttk.Label(
            file_frame, text="No file selected", style="FileLabel.TLabel"
        )
        self.file_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.browse_btn = ttk.Button(
            file_frame,
            text="Browse",
            style="BrowseButton.TButton",
            command=self.browse_file,
        )
        self.browse_btn.grid(row=0, column=1, padx=5, pady=5)
        create_tooltip(self.browse_btn, "Select a video file to process")

        self.refresh_btn = ttk.Button(
            file_frame,
            text="↻",
            width=3,
            style="BrowseButton.TButton",
            command=self.refresh_files,
        )
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        create_tooltip(self.refresh_btn, "Refresh file status")

    def create_parameters_section(self):
        """Create the parameters section"""
        params_frame = ttk.LabelFrame(
            self.upper_frame, text="Segment Detection Parameters", padding="10"
        )
        params_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Store original parameter values for comparison
        self.original_params = {
            "frame_duration": 30,
            "speech_threshold": 75,
            "speech_duration": 50,
            "silence_duration": 300,
        }

        # Row 0: Frame Duration
        ttk.Label(params_frame, text="Frame Duration (ms):").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        self.frame_duration = tk.IntVar(value=30)
        frame_duration_entry = ttk.Spinbox(
            params_frame,
            from_=10,
            to=100,
            textvariable=self.frame_duration,
            width=5,
            command=self.on_parameter_change,
        )
        frame_duration_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        frame_duration_entry.bind("<KeyRelease>", self.on_parameter_change)

        frame_info = InfoIcon(
            params_frame,
            "Duration in milliseconds of each audio frame to analyze.\nShort duration (10-20ms): More precise but slower.\nLong duration (50-100ms): Faster but less precise.",
        )
        frame_info.grid(row=0, column=2, padx=2, pady=5)

        # Row 1: Speech Detection Threshold
        ttk.Label(params_frame, text="Speech Detection (%):").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )

        self.speech_threshold = tk.IntVar(value=75)
        threshold_entry = ttk.Spinbox(
            params_frame,
            from_=1,
            to=100,
            textvariable=self.speech_threshold,
            width=5,
            command=self.on_parameter_change,
        )
        threshold_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        threshold_entry.bind("<KeyRelease>", self.on_parameter_change)

        threshold_info = InfoIcon(
            params_frame,
            "Percentage of frames in a segment that must contain speech.\nHigher values (75-90%): Only strong speech is detected.\nLower values (50-60%): More sensitive, may include ambient sounds.",
        )
        threshold_info.grid(row=1, column=2, padx=2, pady=5)

        # Row 2: Minimum Speech Duration
        ttk.Label(params_frame, text="Min Speech (ms):").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )

        self.min_speech_duration = tk.IntVar(value=50)
        speech_duration_entry = ttk.Spinbox(
            params_frame,
            from_=10,
            to=1000,
            textvariable=self.min_speech_duration,
            width=5,
            command=self.on_parameter_change,
        )
        speech_duration_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        speech_duration_entry.bind("<KeyRelease>", self.on_parameter_change)

        speech_info = InfoIcon(
            params_frame,
            "Minimum duration (ms) for a speech segment to be detected.\nShort duration (30-50ms): Catches short utterances, may include noise.\nLong duration (200-500ms): Only catches sustained speech.",
        )
        speech_info.grid(row=2, column=2, padx=2, pady=5)

        # Row 3: Silence Duration
        ttk.Label(params_frame, text="Min Silence (ms):").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )

        self.min_silence_duration = tk.IntVar(value=300)
        silence_entry = ttk.Spinbox(
            params_frame,
            from_=50,
            to=2000,
            textvariable=self.min_silence_duration,
            width=5,
            command=self.on_parameter_change,
        )
        silence_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        silence_entry.bind("<KeyRelease>", self.on_parameter_change)

        silence_info = InfoIcon(
            params_frame,
            "Minimum duration (ms) of silence to separate segments.\nShort duration (100-200ms): More segments with natural pauses.\nLong duration (500-1000ms): Only significant pauses create new segments.",
        )
        silence_info.grid(row=3, column=2, padx=2, pady=5)

        # Apply button at the bottom
        self.apply_params_btn = ttk.Button(
            params_frame,
            text="Apply Parameters",
            style="Apply.TButton",
            command=self.apply_parameters,
            state="disabled",  # Initially disabled
        )
        self.apply_params_btn.grid(
            row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 5)
        )
        create_tooltip(self.apply_params_btn, "Apply the modified parameters")

    def on_parameter_change(self, event=None):
        """Called when any parameter is changed"""
        current_params = {
            "frame_duration": self.frame_duration.get(),
            "speech_threshold": self.speech_threshold.get(),
            "speech_duration": self.min_speech_duration.get(),
            "silence_duration": self.min_silence_duration.get(),
        }

        # Check if any parameter is different from original
        params_changed = any(
            current_params[key] != self.original_params[key]
            for key in self.original_params
        )

        # Enable apply button only if parameters have changed
        if params_changed:
            self.apply_params_btn.config(state="normal")
        else:
            self.apply_params_btn.config(state="disabled")

    def apply_parameters(self):
        """Apply the currently set parameters"""
        # Update the controller with new parameters
        self.controller.set_segment_params(
            frame_duration=self.frame_duration.get(),
            speech_threshold=self.speech_threshold.get(),
            min_speech_duration=self.min_speech_duration.get(),
            min_silence_duration=self.min_silence_duration.get(),
        )

        # Update original params to match current ones
        self.original_params = {
            "frame_duration": self.frame_duration.get(),
            "speech_threshold": self.speech_threshold.get(),
            "speech_duration": self.min_speech_duration.get(),
            "silence_duration": self.min_silence_duration.get(),
        }

        # Disable the apply button after applying
        self.apply_params_btn.config(state="disabled")

        # Log the applied parameters
        self.controller.log_info("Applied parameters:")
        self.controller.log_info(f"  Frame Duration: {self.frame_duration.get()}ms")
        self.controller.log_info(f"  Speech Threshold: {self.speech_threshold.get()}%")
        self.controller.log_info(
            f"  Min Speech Duration: {self.min_speech_duration.get()}ms"
        )
        self.controller.log_info(
            f"  Min Silence Duration: {self.min_silence_duration.get()}ms"
        )

    def refresh_files(self):
        """Refresh the file status and check for existing files"""
        if self.current_file:
            # Reset status
            self.step1_status.config(text="Not started")
            self.step2_status.config(text="Waiting for segment detection")
            self.step3_status.config(text="Waiting for transcription")
            self.srt_status.config(text="Waiting for suggestions")
            self.video_status.config(text="Waiting for suggestions")

            # Disable processing buttons
            self.step2_btn.config(state="disabled")
            self.step3_btn.config(state="disabled")
            self.srt_btn.config(state="disabled")
            self.video_btn.config(state="disabled")

            # Check for existing files
            self.check_existing_files()

            self.controller.log_info("File status refreshed")
        else:
            self.controller.log_warning("No file selected to refresh")

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
        create_tooltip(
            self.step1_btn, "Detect segments where speech occurs in the video"
        )

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
        create_tooltip(self.step2_btn, "Transcribe the speech segments to text")

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
        create_tooltip(self.step3_btn, "Generate edit suggestions using AI")

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
        create_tooltip(self.srt_btn, "Generate subtitle file from the suggestions")

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
        create_tooltip(self.video_btn, "Create edited video based on the suggestions")

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
            background="#27272A",  # Dark theme background
            foreground="#FFFFFF",  # White text
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10,
            font=("Segoe UI", 9),
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

    def browse_file(self):
        """Open a file dialog to select a video file"""
        video_file = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*")),
        )

        if not video_file:
            return

        # Reset all statuses
        self.step1_status.config(text="Not started")
        self.step2_status.config(text="Waiting for segment detection")
        self.step3_status.config(text="Waiting for transcription")
        self.srt_status.config(text="Waiting for suggestions")
        self.video_status.config(text="Waiting for suggestions")

        # Disable processing buttons
        self.step2_btn.config(state="disabled")
        self.step3_btn.config(state="disabled")
        self.srt_btn.config(state="disabled")
        self.video_btn.config(state="disabled")

        # Set the file and update the UI
        self.current_file = video_file
        self.file_label.config(text=os.path.basename(video_file))
        self.controller.set_video_path(video_file)

        # Enable the first processing button
        self.step1_btn.config(state="normal")

        # Check for existing files
        self.check_existing_files()

        self.controller.log_info(f"Selected video file: {video_file}")

    def check_existing_files(self):
        """Check if JSON files already exist for the selected video and update UI accordingly"""
        if not self.current_file:
            return

        # Check dependencies using the controller
        deps = self.controller.check_dependencies()

        # Update UI based on what files exist
        if deps["segments_detected"]:
            self.step1_status.config(
                text=f"Found: {os.path.basename(self.controller.segments_file)}",
                style="Success.TLabel",
            )
            self.step2_btn.config(state="normal")
            self.controller.log_info(
                f"Found existing segments file: {self.controller.segments_file}"
            )

        if deps["transcription_complete"]:
            self.step2_status.config(
                text=f"Found: {os.path.basename(self.controller.transcription_file)}",
                style="Success.TLabel",
            )
            self.step3_btn.config(state="normal")
            self.controller.log_info(
                f"Found existing transcription file: {self.controller.transcription_file}"
            )

        if deps["suggestion_complete"]:
            self.step3_status.config(
                text=f"Found: {os.path.basename(self.controller.suggestion_file)}",
                style="Success.TLabel",
            )
            self.srt_btn.config(state="normal")
            self.video_btn.config(state="normal")
            self.controller.log_info(
                f"Found existing suggestion file: {self.controller.suggestion_file}"
            )

    def update_button_states(self):
        """Update the enabled/disabled state of the processing buttons"""
        # Enable step 1 if video is selected
        if self.controller.video_path:
            self.step1_btn.config(state="normal")
        else:
            self.step1_btn.config(state="disabled")
            self.step2_btn.config(state="disabled")
            self.step3_btn.config(state="disabled")
            self.srt_btn.config(state="disabled")
            self.video_btn.config(state="disabled")

    def run_detect_segments(self):
        """Run step 1: Detect speech segments"""
        if not self.controller.video_path:
            messagebox.showwarning(
                "No Video Selected", "Please select a video file first."
            )
            return

        # Update parameters
        self.controller.set_segment_params(
            frame_duration=self.frame_duration.get(),
            speech_threshold=self.speech_threshold.get(),
            min_speech_duration=self.min_speech_duration.get(),
            min_silence_duration=self.min_silence_duration.get(),
        )

        # Disable UI during processing
        self.step1_btn.config(state="disabled")
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
            self.step2_btn.config(state="normal")
            self.step2_status.config(text="Ready", style="Status.TLabel")
        else:
            self.step1_status.config(
                text="Failed to detect segments", style="Error.TLabel"
            )
            self.log_message("Segment detection failed - no output file generated")

        # Re-enable the button
        self.step1_btn.config(state="normal")

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
        self.step2_btn.config(state="disabled")
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
            self.step3_btn.config(state="normal")
            self.step3_status.config(text="Ready", style="Status.TLabel")
        else:
            self.step2_status.config(
                text="Failed to transcribe segments", style="Error.TLabel"
            )
            self.log_message("Transcription failed - no output file generated")

        # Re-enable the button
        self.step2_btn.config(state="normal")

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
        self.step3_btn.config(state="disabled")
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
            self.srt_btn.config(state="normal")
            self.srt_status.config(text="Ready", style="Status.TLabel")
            self.video_btn.config(state="normal")
            self.video_status.config(text="Ready", style="Status.TLabel")
        else:
            self.step3_status.config(
                text="Failed to generate suggestions", style="Error.TLabel"
            )
            self.log_message("Suggestion generation failed - no output file generated")

        # Re-enable the button
        self.step3_btn.config(state="normal")

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
        self.srt_btn.config(state="disabled")
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
        self.srt_btn.config(state="normal")

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
        self.video_btn.config(state="disabled")
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
        self.video_btn.config(state="normal")

    def _on_processing_error(self, error_msg):
        """Handle processing errors"""
        self.processing = False
        logging.error(error_msg)
        self.log_message(error_msg)

        # Ensure all buttons are enabled
        self.step1_btn.config(state="normal")
        if hasattr(self, "step2_btn"):
            self.step2_btn.config(state="normal")
        if hasattr(self, "step3_btn"):
            self.step3_btn.config(state="normal")
        if hasattr(self, "srt_btn"):
            self.srt_btn.config(state="normal")
        if hasattr(self, "video_btn"):
            self.video_btn.config(state="normal")

        # Show error message
        messagebox.showerror("Processing Error", error_msg)

    def update_log(self, message):
        """Update the log with a message from the controller

        Args:
            message: Message to add to the log
        """
        self.log_message(message)
