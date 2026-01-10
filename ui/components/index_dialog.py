"""
QID - Index Dialog Component
Dialog for indexing images from a folder.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading


class IndexDialog:
    """
    Dialog window for batch indexing images.
    
    Features:
    - Folder selection
    - Options (recursive, validate, skip existing)
    - Progress bar
    - Real-time status updates
    """
    
    def __init__(self, parent, batch_indexer, on_complete=None):
        """
        Initialize index dialog.
        
        Args:
            parent: Parent window
            batch_indexer: BatchIndexer instance
            on_complete: Callback function(stats: dict)
        """
        self.parent = parent
        self.batch_indexer = batch_indexer
        self.on_complete = on_complete
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Index Images")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f'+{x}+{y}')
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Folder selection frame
        self.folder_frame = ttk.LabelFrame(self.dialog, text="Folder Selection", padding=10)
        
        self.folder_var = tk.StringVar(value="data/images")
        folder_entry = ttk.Entry(self.folder_frame, textvariable=self.folder_var, width=40)
        browse_btn = ttk.Button(self.folder_frame, text="Browse...", command=self._browse_folder)
        
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_btn.pack(side=tk.RIGHT)
        
        # Options frame
        self.options_frame = ttk.LabelFrame(self.dialog, text="Options", padding=10)
        
        self.recursive_var = tk.BooleanVar(value=True)
        self.validate_var = tk.BooleanVar(value=True)
        self.skip_existing_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(
            self.options_frame,
            text="Include subfolders",
            variable=self.recursive_var
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            self.options_frame,
            text="Validate images",
            variable=self.validate_var
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            self.options_frame,
            text="Skip already-indexed images",
            variable=self.skip_existing_var
        ).pack(anchor=tk.W, pady=2)
        
        # Progress frame
        self.progress_frame = ttk.LabelFrame(self.dialog, text="Progress", padding=10)
        
        self.status_label = ttk.Label(self.progress_frame, text="Ready to index")
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.details_label = ttk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        self.details_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Buttons frame
        self.buttons_frame = ttk.Frame(self.dialog, padding=10)
        
        self.start_btn = ttk.Button(
            self.buttons_frame,
            text="Start Indexing",
            command=self._start_indexing
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(
            self.buttons_frame,
            text="Close",
            command=self.dialog.destroy
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def _setup_layout(self):
        """Arrange widgets."""
        self.folder_frame.pack(fill=tk.X, padx=10, pady=10)
        self.options_frame.pack(fill=tk.X, padx=10, pady=10)
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.buttons_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def _browse_folder(self):
        """Open folder selection dialog."""
        folder = filedialog.askdirectory(
            title="Select Image Folder",
            initialdir=self.folder_var.get()
        )
        
        if folder:
            self.folder_var.set(folder)
    
    def _start_indexing(self):
        """Start indexing in background thread."""
        folder = self.folder_var.get()
        
        if not folder:
            messagebox.showwarning("No Folder", "Please select a folder")
            return
        
        # Disable controls
        self.start_btn.config(state='disabled')
        
        # Start progress animation
        self.progress_bar.start()
        self.status_label.config(text="Indexing...")
        
        # Run in background thread
        thread = threading.Thread(target=self._index_thread, args=(folder,))
        thread.daemon = True
        thread.start()
    
    def _index_thread(self, folder):
        """
        Background thread for indexing.
        
        Args:
            folder: Folder path to index
        """
        try:
            # Index images
            stats = self.batch_indexer.index_directory(
                folder,
                recursive=self.recursive_var.get(),
                validate=self.validate_var.get(),
                skip_existing=self.skip_existing_var.get()
            )
            
            # Update UI on main thread
            self.dialog.after(0, lambda: self._on_indexing_complete(stats))
            
        except Exception as e:
            self.dialog.after(0, lambda: self._on_indexing_error(str(e)))
    
    def _on_indexing_complete(self, stats):
        """
        Called when indexing completes successfully.
        
        Args:
            stats: Indexing statistics dictionary
        """
        # Stop progress
        self.progress_bar.stop()
        self.progress_bar['mode'] = 'determinate'
        self.progress_var.set(100)
        
        # Update status
        self.status_label.config(text="✅ Indexing complete!")
        self.details_label.config(
            text=f"Processed: {stats['processed']} | Total: {stats['found']}"
        )
        
        # Re-enable close button
        self.cancel_btn.config(text="Close")
        
        # Call completion callback
        if self.on_complete:
            self.on_complete(stats)
    
    def _on_indexing_error(self, error):
        """
        Called when indexing fails.
        
        Args:
            error: Error message
        """
        # Stop progress
        self.progress_bar.stop()
        
        # Update status
        self.status_label.config(text="❌ Indexing failed")
        self.details_label.config(text=f"Error: {error}")
        
        # Re-enable controls
        self.start_btn.config(state='normal')
        
        messagebox.showerror("Indexing Error", f"Failed to index:\n{error}")