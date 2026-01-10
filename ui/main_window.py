"""
QID - Main Window
Primary application window with search and navigation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from .components.search_panel import SearchPanel
from .components.image_grid import ImageGrid
from .components.status_bar import StatusBar
from .components.index_dialog import IndexDialog


class MainWindow:
    """
    Main application window.
    
    Layout:
    ┌─────────────────────────────────────┐
    │ Menu Bar                            │
    ├─────────────────────────────────────┤
    │ Search Panel (query input)          │
    ├─────────────────────────────────────┤
    │                                     │
    │         Image Grid                  │
    │         (search results)            │
    │                                     │
    ├─────────────────────────────────────┤
    │ Status Bar (stats, messages)        │
    └─────────────────────────────────────┘
    """
    
    def __init__(self, root, search_engine, batch_indexer, config):
        """
        Initialize main window.
        
        Args:
            root: Tk root window
            search_engine: SearchEngine instance
            batch_indexer: BatchIndexer instance
            config: Config instance
        """
        self.root = root
        self.search_engine = search_engine
        self.batch_indexer = batch_indexer
        self.config = config
        
        # Configure window
        self.root.title(config.get('ui.window_title'))
        
        # Parse window size
        size = config.get('ui.window_size')
        self.root.geometry(size)
        
        # Setup UI
        self._create_menu()
        self._create_widgets()
        self._setup_layout()
        
        # Load initial state
        self._update_stats()
        
        # Show welcome message if database is empty
        if len(self.batch_indexer.metadata_store) == 0:
            self._show_welcome()
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Index Folder...", command=self._index_folder)
        file_menu.add_command(label="Index Single Image...", command=self._index_single)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Database menu
        db_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Database", menu=db_menu)
        db_menu.add_command(label="Statistics", command=self._show_stats)
        db_menu.add_command(label="Clear Database...", command=self._clear_database)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Quick Start", command=self._show_quickstart)
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Search panel
        self.search_panel = SearchPanel(
            self.root,
            on_search=self._on_search
        )
        
        # Image grid (scrollable)
        self.image_grid = ImageGrid(
            self.root,
            columns=self.config.get('ui.grid_columns'),
            thumbnail_size=self.config.get('ui.preview_size')
        )
        
        # Status bar
        self.status_bar = StatusBar(self.root)
    
    def _setup_layout(self):
        """Arrange widgets in window."""
        # Search panel at top
        self.search_panel.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Status bar at bottom
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Image grid fills remaining space
        self.image_grid.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def _on_search(self, query):
        """
        Handle search query.
        
        Args:
            query: Search query string
        """
        if not query.strip():
            return
        
        # Update status
        self.status_bar.set_message(f"Searching for: '{query}'...")
        self.root.update()
        
        try:
            # Perform search with adaptive threshold
            results = self.search_engine.search(
                query,
                top_k=50,  # Get up to 50, but adaptive filter will reduce
                adaptive_threshold=True
            )
            
            if not results:
                self.status_bar.set_message(f"No results found for: '{query}'")
                self.image_grid.clear()
                messagebox.showinfo("No Results", f"No images found matching '{query}'")
                return
            
            # Display results
            self.image_grid.display_results(results)
            
            # Update status
            self.status_bar.set_message(
                f"Found {len(results)} results for: '{query}' "
                f"(best match: {results[0]['score']:.1%})"
            )
            
        except Exception as e:
            messagebox.showerror("Search Error", f"Search failed:\n{e}")
            self.status_bar.set_message("Search failed")
    
    def _index_folder(self):
        """Open dialog to index a folder."""
        dialog = IndexDialog(
            self.root,
            self.batch_indexer,
            on_complete=self._on_index_complete
        )
    
    def _index_single(self):
        """Index a single image file."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Update status
        self.status_bar.set_message(f"Indexing: {Path(file_path).name}...")
        self.root.update()
        
        try:
            success = self.batch_indexer.index_single_image(file_path)
            
            if success:
                messagebox.showinfo("Success", f"Image indexed successfully!")
                self._update_stats()
            else:
                messagebox.showwarning("Already Indexed", "Image already in database")
            
        except Exception as e:
            messagebox.showerror("Indexing Error", f"Failed to index image:\n{e}")
        
        self.status_bar.set_message("Ready")
    
    def _on_index_complete(self, stats):
        """
        Called when indexing completes.
        
        Args:
            stats: Dictionary with indexing statistics
        """
        self._update_stats()
        
        messagebox.showinfo(
            "Indexing Complete",
            f"Processed {stats['processed']} images\n"
            f"Total in database: {len(self.batch_indexer.metadata_store)}"
        )
    
    def _update_stats(self):
        """Update status bar statistics."""
        total = len(self.batch_indexer.metadata_store)
        self.status_bar.set_stats(f"Database: {total:,} images")
    
    def _show_stats(self):
        """Show detailed database statistics."""
        stats = self.batch_indexer.get_stats()
        tags = self.search_engine.get_all_tags()
        
        msg = (
            f"Database Statistics\n\n"
            f"Total Images: {stats['total_images']:,}\n"
            f"Total Vectors: {stats['total_vectors']:,}\n"
            f"Vector Dimension: {stats['vector_dimension']}\n"
            f"Index Type: {stats['index_type']}\n"
            f"Unique Tags: {len(tags)}\n"
        )
        
        messagebox.showinfo("Statistics", msg)
    
    def _clear_database(self):
        """Clear all data from database."""
        result = messagebox.askyesno(
            "Clear Database",
            "This will delete all indexed images!\n\n"
            "Are you sure you want to continue?",
            icon='warning'
        )
        
        if result:
            # Double confirmation
            result2 = messagebox.askyesno(
                "Confirm",
                "Really delete everything?\n"
                "This cannot be undone!",
                icon='warning'
            )
            
            if result2:
                self.batch_indexer.vector_store.clear()
                self.batch_indexer.metadata_store.clear()
                self.image_grid.clear()
                self._update_stats()
                
                messagebox.showinfo("Success", "Database cleared")
    
    def _show_about(self):
        """Show about dialog."""
        msg = (
            "QID - Query Images by Description\n\n"
            "Version 1.0.0\n\n"
            "A semantic image search system powered by\n"
            "OpenAI's CLIP model.\n\n"
            "Find images using natural language descriptions!"
        )
        messagebox.showinfo("About QID", msg)
    
    def _show_quickstart(self):
        """Show quick start guide."""
        msg = (
            "Quick Start Guide\n\n"
            "1. Index Images:\n"
            "   File → Index Folder → Select folder with images\n\n"
            "2. Search:\n"
            "   Type natural language query in search box\n"
            "   Example: 'sunset at the beach'\n\n"
            "3. View Results:\n"
            "   Click on any image to view full size\n\n"
            "4. Tips:\n"
            "   - Be descriptive: 'a dog playing in a park'\n"
            "   - Use concepts: 'happy people', 'peaceful nature'\n"
            "   - Try colors: 'blue water', 'orange sunset'"
        )
        messagebox.showinfo("Quick Start", msg)
    
    def _show_welcome(self):
        """Show welcome message for first-time users."""
        msg = (
            "Welcome to QID!\n\n"
            "Your database is empty.\n\n"
            "Get started by indexing some images:\n"
            "File → Index Folder\n\n"
            "Or try the test images:\n"
            "1. Run: python create_test_images.py\n"
            "2. Then index the 'data/images' folder"
        )
        messagebox.showinfo("Welcome", msg)