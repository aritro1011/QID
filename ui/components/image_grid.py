"""
QID - Image Grid Component
Displays search results as a grid of thumbnails.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
import os


class ImageGrid(ttk.Frame):
    """
    Scrollable grid of image thumbnails.
    
    Displays search results with:
    - Thumbnail image
    - Filename
    - Similarity score
    - Click to view full size
    """
    
    def __init__(self, parent, columns=4, thumbnail_size=200):
        """
        Initialize image grid.
        
        Args:
            parent: Parent widget
            columns: Number of columns in grid
            thumbnail_size: Size of thumbnails in pixels
        """
        super().__init__(parent)
        
        self.columns = columns
        self.thumbnail_size = thumbnail_size
        self.results = []
        self.photo_images = []  # Keep references to prevent garbage collection
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create scrollable canvas."""
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(self, bg='#f0f0f0', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        
        # Frame inside canvas for grid
        self.grid_frame = ttk.Frame(self.canvas)
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.grid_frame,
            anchor=tk.NW
        )
        
        # Bind resize
        self.grid_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Bind mousewheel
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
    
    def _setup_layout(self):
        """Arrange widgets."""
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _on_frame_configure(self, event=None):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        """Update canvas window width when canvas resizes."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def display_results(self, results):
        """
        Display search results in grid.
        
        Args:
            results: List of result dictionaries from search engine
        """
        # Clear existing
        self.clear()
        
        self.results = results
        
        # Create grid items
        for i, result in enumerate(results):
            row = i // self.columns
            col = i % self.columns
            
            self._create_grid_item(result, row, col)
        
        # Scroll to top
        self.canvas.yview_moveto(0)
    
    def _create_grid_item(self, result, row, col):
        """
        Create a single grid item (thumbnail + info).
        
        Args:
            result: Result dictionary
            row: Grid row
            col: Grid column
        """
        # Container frame
        item_frame = ttk.Frame(self.grid_frame, relief=tk.RAISED, borderwidth=1)
        item_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        # Load and resize image
        try:
            img_path = result['file_path']
            
            # Check if file exists
            if not Path(img_path).exists():
                # Show placeholder
                self._create_placeholder(item_frame, "File not found")
                return
            
            # Load image
            img = Image.open(img_path)
            
            # Resize maintaining aspect ratio
            img.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.photo_images.append(photo)  # Keep reference
            
            # Image label
            img_label = ttk.Label(item_frame, image=photo)
            img_label.pack(padx=5, pady=5)
            
            # Make clickable
            img_label.bind('<Button-1>', lambda e, p=img_path: self._on_image_click(p))
            img_label.configure(cursor='hand2')
            
        except Exception as e:
            self._create_placeholder(item_frame, f"Error: {str(e)[:20]}")
        
        # Filename
        filename_label = ttk.Label(
            item_frame,
            text=result['file_name'],
            font=('Arial', 9),
            wraplength=self.thumbnail_size
        )
        filename_label.pack(pady=(0, 2))
        
        # Score
        score_text = f"Match: {result['score']:.1%}"
        score_label = ttk.Label(
            item_frame,
            text=score_text,
            font=('Arial', 8, 'bold'),
            foreground='green' if result['score'] > 0.8 else 'orange'
        )
        score_label.pack(pady=(0, 5))
    
    def _create_placeholder(self, parent, text):
        """Create placeholder for missing images."""
        placeholder = tk.Canvas(parent, width=self.thumbnail_size, height=self.thumbnail_size, bg='gray')
        placeholder.pack(padx=5, pady=5)
        
        placeholder.create_text(
            self.thumbnail_size // 2,
            self.thumbnail_size // 2,
            text=text,
            fill='white',
            font=('Arial', 10)
        )
    
    def _on_image_click(self, image_path):
        """
        Handle image click - open in system viewer.
        
        Args:
            image_path: Path to image file
        """
        try:
            # Open with default system viewer
            if os.name == 'nt':  # Windows
                os.startfile(image_path)
            elif os.name == 'posix':  # macOS/Linux
                import subprocess
                subprocess.call(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', image_path])
        except Exception as e:
            print(f"Failed to open image: {e}")
    
    def clear(self):
        """Clear all grid items."""
        # Clear photo references
        self.photo_images.clear()
        
        # Destroy all children
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        self.results = []