"""
QID - Status Bar Component
Displays status messages and statistics.
"""

import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    """
    Status bar at bottom of window.
    
    Shows: [Message] | [Statistics]
    """
    
    def __init__(self, parent):
        """
        Initialize status bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, relief=tk.SUNKEN)
        
        self._create_widgets()
        self._setup_layout()
        
        self.set_message("Ready")
    
    def _create_widgets(self):
        """Create status labels."""
        # Message label (left)
        self.message_label = ttk.Label(
            self,
            text="",
            font=('Arial', 9),
            anchor=tk.W
        )
        
        # Separator
        self.separator = ttk.Separator(self, orient=tk.VERTICAL)
        
        # Stats label (right)
        self.stats_label = ttk.Label(
            self,
            text="",
            font=('Arial', 9),
            anchor=tk.E
        )
    
    def _setup_layout(self):
        """Arrange widgets."""
        self.message_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=2)
        self.separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.stats_label.pack(side=tk.RIGHT, padx=10, pady=2)
    
    def set_message(self, message):
        """
        Set status message.
        
        Args:
            message: Message text
        """
        self.message_label.config(text=message)
    
    def set_stats(self, stats):
        """
        Set statistics text.
        
        Args:
            stats: Statistics text
        """
        self.stats_label.config(text=stats)