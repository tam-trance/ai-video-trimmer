"""
UI Components module for the Video Processor Application.

This module provides reusable UI components that can be used across the application.
"""

import os
import platform
import subprocess
import sys
import tkinter as tk
from tkinter import ttk


class FolderButton:
    """A button that opens a folder in the file explorer"""

    def __init__(self, parent, folder_path, tooltip_text="Open folder", **kwargs):
        """Initialize a folder button

        Args:
            parent: The parent widget
            folder_path: The path to the folder to open
            tooltip_text: The tooltip text to display
            **kwargs: Additional arguments to pass to the button
        """
        self.parent = parent
        self.folder_path = folder_path

        # Create the button with a folder icon
        icon = "📁" if platform.system() == "Windows" else "📂"
        self.button = ttk.Button(
            parent,
            text=icon,
            style="Folder.TButton",
            command=self.open_folder,
            width=2,
            **kwargs,
        )

        # Create tooltip on hover
        from src.gui.tooltips import create_tooltip

        create_tooltip(self.button, tooltip_text)

    def open_folder(self):
        """Open the folder in the file explorer"""
        folder_path = self.folder_path

        # Make sure the folder exists
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        try:
            # Open the folder using the system's file explorer
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            print(f"Error opening folder: {e}")

    def grid(self, **kwargs):
        """Grid the button in the parent widget"""
        self.button.grid(**kwargs)

    def pack(self, **kwargs):
        """Pack the button in the parent widget"""
        self.button.pack(**kwargs)

    def place(self, **kwargs):
        """Place the button in the parent widget"""
        self.button.place(**kwargs)

    def configure(self, **kwargs):
        """Configure the button"""
        if "folder_path" in kwargs:
            self.folder_path = kwargs.pop("folder_path")
        self.button.configure(**kwargs)


class InfoIcon:
    """An information icon with tooltip"""

    def __init__(self, parent, tooltip_text, **kwargs):
        """Initialize an information icon

        Args:
            parent: The parent widget
            tooltip_text: The tooltip text to display
            **kwargs: Additional arguments to pass to the label
        """
        self.parent = parent
        self.tooltip_text = tooltip_text

        # Frame to hold the icon for better visibility
        self.frame = ttk.Frame(parent)

        # Create the label with a clear info icon - use a button instead of a label for better interactivity
        self.button = ttk.Button(
            self.frame,
            text="?",
            style="Icon.TButton",
            width=1,
            cursor="question_arrow",
            **kwargs,
        )
        self.button.pack(pady=0, padx=0)

        # Create tooltip on hover with reduced delay for better responsiveness
        from src.gui.tooltips import create_tooltip

        self.tooltip = create_tooltip(self.button, tooltip_text, delay=300)

        # Additional binding to ensure tooltip shows
        self.button.bind("<Enter>", self._on_enter)
        self.button.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Handle mouse enter event to ensure tooltip displays"""
        # Additional code to make sure tooltip will show
        if hasattr(self.tooltip, "schedule"):
            self.tooltip.schedule()

    def _on_leave(self, event):
        """Handle mouse leave event to ensure tooltip hides"""
        if hasattr(self.tooltip, "hide"):
            self.tooltip.hide()

    def grid(self, **kwargs):
        """Grid the frame in the parent widget"""
        self.frame.grid(**kwargs)

    def pack(self, **kwargs):
        """Pack the frame in the parent widget"""
        self.frame.pack(**kwargs)

    def place(self, **kwargs):
        """Place the frame in the parent widget"""
        self.frame.place(**kwargs)
