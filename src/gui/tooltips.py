"""
Tooltips module for creating hover tooltips on tkinter widgets.
"""

import tkinter as tk


class Tooltip:
    """
    Creates a tooltip for a given widget.

    Parameters:
        widget: The widget to add the tooltip to
        text: The text to display
        delay: Delay in milliseconds before the tooltip appears
        wraplength: Maximum width of tooltip text before wrapping
    """

    def __init__(self, widget, text, delay=500, wraplength=250, **kwargs):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.tooltip_window = None
        self.id = None

        # Bind events
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<ButtonPress>", self.hide)

    def schedule(self, event=None):
        """Schedule the tooltip to appear after delay"""
        self.id = self.widget.after(self.delay, self.show)

    def show(self):
        """Display the tooltip"""
        # Get screen position
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")

        # Create tooltip label with dark theme colors
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#27272A",  # Dark background
            foreground="#FFFFFF",  # White text
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=self.wraplength,
            padx=8,
            pady=6,
            font=("Segoe UI", 9),
        )
        label.pack(fill=tk.BOTH, expand=True)

        # Add a subtle border
        tw.configure(background="#5b79ff")  # Primary color border

        # Make sure tooltip stays on top
        tw.attributes("-topmost", True)

    def hide(self, event=None):
        """Hide the tooltip"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def create_tooltip(widget, text, delay=500, wraplength=250):
    """
    Create a tooltip for a widget

    Args:
        widget: The widget to add the tooltip to
        text: The text to display
        delay: Delay in milliseconds before the tooltip appears
        wraplength: Maximum width of tooltip text before wrapping

    Returns:
        The Tooltip object
    """
    tooltip = Tooltip(widget, text, delay, wraplength)
    return tooltip
