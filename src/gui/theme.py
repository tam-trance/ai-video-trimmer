"""
Theme module for styling the application UI.

This module provides a modern, Shadcn UI-like style for Tkinter widgets.
"""

import platform
import tkinter as tk
from tkinter import ttk


class ShadcnTheme:
    """A theme class that applies Shadcn UI-like styling to Tkinter widgets"""

    # Color palette - DARK THEME
    COLORS = {
        "background": "#111111",  # Dark background
        "foreground": "#FFFFFF",  # White text
        "primary": "#5b79ff",  # Blue primary color as requested
        "primary_hover": "#4a68ee",  # Slightly darker blue
        "primary_active": "#3957dd",  # Even darker blue
        "secondary": "#2D2D30",  # Dark grey for secondary elements
        "secondary_hover": "#3E3E42",  # Slightly lighter grey
        "secondary_active": "#505054",  # Even lighter grey
        "success": "#4CC38A",  # Brighter green for dark mode
        "info": "#5B9BD5",  # Brighter blue for dark mode
        "warning": "#FFC107",  # Brighter yellow for dark mode
        "error": "#FF5252",  # Brighter red for dark mode
        "surface": "#1E1E1E",  # Slightly lighter than background
        "border": "#3E3E42",  # Dark border color
        "muted": "#727272",  # Muted text color
        "muted_foreground": "#AAAAAA",  # Light grey for less important text
    }

    # Font configurations
    FONTS = {
        "default": ("Segoe UI" if platform.system() == "Windows" else "Helvetica", 10),
        "heading": (
            "Segoe UI" if platform.system() == "Windows" else "Helvetica",
            12,
            "bold",
        ),
        "subheading": (
            "Segoe UI" if platform.system() == "Windows" else "Helvetica",
            11,
            "bold",
        ),
        "caption": ("Segoe UI" if platform.system() == "Windows" else "Helvetica", 9),
        "button": ("Segoe UI" if platform.system() == "Windows" else "Helvetica", 10),
    }

    def __init__(self, root):
        """Initialize the theme

        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.style = ttk.Style()
        self.configure_theme()

    def configure_theme(self):
        """Apply the theme to all widgets"""
        # Try to use a modern theme as base
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass  # Fall back to default if clam is not available

        # Configure the root window
        self.root.configure(bg=self.COLORS["background"])

        # Configure ttk styles
        self._configure_frames()
        self._configure_buttons()
        self._configure_labels()
        self._configure_entries()
        self._configure_combobox()
        self._configure_spinbox()
        self._configure_progressbar()
        self._configure_notebook()
        self._configure_treeview()
        self._configure_scrollbar()

    def _configure_frames(self):
        """Configure frame styles"""
        # Main frame
        self.style.configure(
            "TFrame",
            background=self.COLORS["background"],
        )

        # LabelFrame
        self.style.configure(
            "TLabelframe",
            background=self.COLORS["background"],
            borderwidth=1,
            relief="solid",
            bordercolor=self.COLORS["border"],
        )
        self.style.configure(
            "TLabelframe.Label",
            background=self.COLORS["background"],
            foreground=self.COLORS["foreground"],
            font=self.FONTS["subheading"],
            padding=(10, 5),
        )

    def _configure_buttons(self):
        """Configure button styles"""
        # Primary button
        self.style.configure(
            "Primary.TButton",
            background=self.COLORS["primary"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            focuscolor=self.COLORS["primary"],
            padding=(12, 8),
            font=self.FONTS["button"],
            relief="flat",
        )
        self.style.map(
            "Primary.TButton",
            background=[
                ("active", self.COLORS["primary_hover"]),
                ("pressed", self.COLORS["primary_active"]),
                ("disabled", self.COLORS["muted"]),
            ],
            foreground=[("disabled", "#FFFFFF")],
        )

        # Secondary button
        self.style.configure(
            "Secondary.TButton",
            background=self.COLORS["secondary"],
            foreground=self.COLORS["foreground"],
            borderwidth=0,
            focusthickness=0,
            focuscolor=self.COLORS["secondary"],
            padding=(12, 8),
            font=self.FONTS["button"],
            relief="flat",
        )
        self.style.map(
            "Secondary.TButton",
            background=[
                ("active", self.COLORS["secondary_hover"]),
                ("pressed", self.COLORS["secondary_active"]),
                ("disabled", self.COLORS["muted"]),
            ],
            foreground=[("disabled", self.COLORS["muted_foreground"])],
        )

        # Outline button
        self.style.configure(
            "Outline.TButton",
            background=self.COLORS["background"],
            foreground=self.COLORS["primary"],
            borderwidth=1,
            bordercolor=self.COLORS["primary"],
            focusthickness=0,
            focuscolor=self.COLORS["primary"],
            padding=(12, 8),
            font=self.FONTS["button"],
            relief="solid",
        )
        self.style.map(
            "Outline.TButton",
            background=[
                ("active", self.COLORS["secondary"]),
                ("pressed", self.COLORS["secondary_hover"]),
                ("disabled", self.COLORS["background"]),
            ],
            foreground=[
                ("disabled", self.COLORS["muted"]),
            ],
        )

        # Icon button (small button for icons)
        self.style.configure(
            "Icon.TButton",
            background=self.COLORS["background"],
            foreground=self.COLORS["foreground"],
            borderwidth=0,
            focusthickness=0,
            padding=(6, 6),
            relief="flat",
        )
        self.style.map(
            "Icon.TButton",
            background=[
                ("active", self.COLORS["secondary"]),
                ("pressed", self.COLORS["secondary_hover"]),
            ],
        )

        # Processing button (used for main processing steps)
        self.style.configure(
            "Processing.TButton",
            background=self.COLORS["primary"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(15, 10),
            font=(
                "Segoe UI" if platform.system() == "Windows" else "Helvetica",
                11,
                "bold",
            ),
            relief="flat",
            width=20,  # Fixed width for consistency
        )
        self.style.map(
            "Processing.TButton",
            background=[
                ("active", self.COLORS["primary_hover"]),
                ("pressed", self.COLORS["primary_active"]),
                ("disabled", self.COLORS["muted"]),
            ],
        )

        # Folder button (used to open folders)
        self.style.configure(
            "Folder.TButton",
            background=self.COLORS["info"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(5, 5),
            relief="flat",
            width=2,  # Fixed width for consistency
        )
        self.style.map(
            "Folder.TButton",
            background=[
                ("active", "#4a68ee"),  # Slightly darker blue
                ("pressed", "#3957dd"),  # Even darker blue
                ("disabled", self.COLORS["muted"]),
            ],
        )

    def _configure_labels(self):
        """Configure label styles"""
        # Default label
        self.style.configure(
            "TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["foreground"],
            font=self.FONTS["default"],
            padding=5,
        )

        # Header label
        self.style.configure(
            "Header.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["foreground"],
            font=self.FONTS["heading"],
            padding=10,
        )

        # Subheader label
        self.style.configure(
            "Subheader.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["foreground"],
            font=self.FONTS["subheading"],
            padding=5,
        )

        # Status labels
        self.style.configure(
            "Status.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["muted_foreground"],
            font=self.FONTS["caption"],
            padding=5,
        )

        self.style.configure(
            "Success.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["success"],
            font=self.FONTS["caption"],
            padding=5,
        )

        self.style.configure(
            "Info.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["info"],
            font=self.FONTS["caption"],
            padding=5,
        )

        self.style.configure(
            "Warning.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["warning"],
            font=self.FONTS["caption"],
            padding=5,
        )

        self.style.configure(
            "Error.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["error"],
            font=self.FONTS["caption"],
            padding=5,
        )

        # Info icon label
        self.style.configure(
            "Info.Icon.TLabel",
            background=self.COLORS["background"],
            foreground=self.COLORS["info"],
            font=("Segoe UI" if platform.system() == "Windows" else "Helvetica", 12),
        )

    def _configure_entries(self):
        """Configure entry styles"""
        self.style.configure(
            "TEntry",
            foreground=self.COLORS["foreground"],
            fieldbackground=self.COLORS["surface"],
            borderwidth=1,
            bordercolor=self.COLORS["border"],
            lightcolor=self.COLORS["surface"],
            darkcolor=self.COLORS["surface"],
            insertcolor=self.COLORS["foreground"],
            padding=8,
        )
        self.style.map(
            "TEntry",
            bordercolor=[("focus", self.COLORS["primary"])],
            lightcolor=[("focus", self.COLORS["primary"])],
            darkcolor=[("focus", self.COLORS["primary"])],
        )

    def _configure_combobox(self):
        """Configure combobox styles"""
        self.style.configure(
            "TCombobox",
            foreground=self.COLORS["foreground"],
            fieldbackground=self.COLORS["surface"],
            background=self.COLORS["surface"],
            borderwidth=1,
            bordercolor=self.COLORS["border"],
            padding=8,
            arrowsize=15,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", self.COLORS["surface"]),
                ("disabled", self.COLORS["secondary"]),
            ],
            bordercolor=[("focus", self.COLORS["primary"])],
        )

    def _configure_spinbox(self):
        """Configure spinbox styles"""
        self.style.configure(
            "TSpinbox",
            foreground=self.COLORS["foreground"],
            fieldbackground=self.COLORS["surface"],
            background=self.COLORS["surface"],
            borderwidth=1,
            bordercolor=self.COLORS["border"],
            padding=8,
            arrowsize=12,
        )
        self.style.map(
            "TSpinbox",
            fieldbackground=[("readonly", self.COLORS["surface"])],
            bordercolor=[("focus", self.COLORS["primary"])],
        )

    def _configure_progressbar(self):
        """Configure progressbar styles"""
        self.style.configure(
            "TProgressbar",
            thickness=10,
            borderwidth=0,
            troughcolor=self.COLORS["secondary"],
            background=self.COLORS["primary"],
        )

    def _configure_notebook(self):
        """Configure notebook styles"""
        self.style.configure(
            "TNotebook",
            background=self.COLORS["background"],
            tabmargins=[2, 5, 2, 0],
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            background=self.COLORS["secondary"],
            foreground=self.COLORS["foreground"],
            borderwidth=0,
            font=self.FONTS["default"],
            padding=[10, 5],
        )
        self.style.map(
            "TNotebook.Tab",
            background=[
                ("selected", self.COLORS["background"]),
                ("active", self.COLORS["secondary_hover"]),
            ],
            foreground=[("selected", self.COLORS["primary"])],
        )

    def _configure_treeview(self):
        """Configure treeview styles"""
        self.style.configure(
            "Treeview",
            background=self.COLORS["surface"],
            fieldbackground=self.COLORS["surface"],
            foreground=self.COLORS["foreground"],
            borderwidth=0,
            font=self.FONTS["default"],
            rowheight=25,
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.COLORS["background"],
            foreground=self.COLORS["foreground"],
            font=self.FONTS["subheading"],
            padding=5,
            borderwidth=0,
        )
        self.style.map(
            "Treeview",
            background=[("selected", self.COLORS["primary"])],
            foreground=[("selected", "white")],
        )

    def _configure_scrollbar(self):
        """Configure scrollbar styles"""
        self.style.configure(
            "TScrollbar",
            background=self.COLORS["surface"],
            troughcolor=self.COLORS["background"],
            borderwidth=0,
            arrowsize=12,
        )
        self.style.map(
            "TScrollbar",
            background=[
                ("active", self.COLORS["secondary_hover"]),
                ("pressed", self.COLORS["secondary_active"]),
            ],
        )

    def get_color(self, color_name):
        """Get a color from the color palette

        Args:
            color_name: The name of the color

        Returns:
            The color value
        """
        return self.COLORS.get(color_name, self.COLORS["foreground"])

    def get_font(self, font_name):
        """Get a font from the font configurations

        Args:
            font_name: The name of the font

        Returns:
            The font value
        """
        return self.FONTS.get(font_name, self.FONTS["default"])
