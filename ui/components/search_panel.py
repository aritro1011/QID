"""
QID - Search Panel Component
Search bar with query input and search button.
"""

import tkinter as tk
from tkinter import ttk


class SearchPanel(ttk.Frame):
    """
    Search panel with input field and button.
    
    Layout: [Search: ________________] [🔍 Search]
    """
    
    def __init__(self, parent, on_search=None):
        """
        Initialize search panel.
        
        Args:
            parent: Parent widget
            on_search: Callback function(query: str)
        """
        super().__init__(parent)
        
        self.on_search = on_search
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create search widgets."""
        # Label
        self.label = ttk.Label(self, text="Search:", font=('Arial', 11))
        
        # Entry field
        self.search_var = tk.StringVar()
        self.entry = ttk.Entry(
            self,
            textvariable=self.search_var,
            font=('Arial', 11),
            width=60
        )
        
        # Bind Enter key
        self.entry.bind('<Return>', lambda e: self._do_search())
        
        # Search button
        self.search_button = ttk.Button(
            self,
            text="🔍 Search",
            command=self._do_search
        )
        
        # Clear button
        self.clear_button = ttk.Button(
            self,
            text="✕ Clear",
            command=self._clear_search
        )
    
    def _setup_layout(self):
        """Arrange widgets."""
        self.label.pack(side=tk.LEFT, padx=(0, 10))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_button.pack(side=tk.LEFT, padx=5)
        self.clear_button.pack(side=tk.LEFT)
        
        # Focus on entry
        self.entry.focus()
    
    def _do_search(self):
        """Execute search."""
        query = self.search_var.get().strip()
        
        if query and self.on_search:
            self.on_search(query)
    
    def _clear_search(self):
        """Clear search field."""
        self.search_var.set("")
        self.entry.focus()
    
    def get_query(self):
        """Get current query text."""
        return self.search_var.get().strip()
    
    def set_query(self, query):
        """Set query text."""
        self.search_var.set(query)