"""
QID - Main Application
Tkinter-based GUI for semantic image search.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    ImageEncoder, TextEncoder,
    VectorStore, MetadataStore,
    BatchIndexer, SearchEngine,
    get_config, setup_logging, get_logger
)

from ui.main_window import MainWindow


class QIDApp:
    """
    Main QID Application.
    
    Initializes all components and launches the UI.
    """
    
    def __init__(self):
        """Initialize the application."""
        # Load configuration
        self.config = get_config()
        
        # Setup logging
        setup_logging(
            log_file=self.config.get('logging.file'),
            level=self.config.get('logging.level'),
            console=False  # Don't clutter UI with console logs
        )
        
        self.logger = get_logger(__name__)
        self.logger.info("Starting QID application")
        
        # Initialize AI components
        self._init_components()
        
        # Create main window
        self.root = tk.Tk()
        self.main_window = MainWindow(
            self.root,
            search_engine=self.search_engine,
            batch_indexer=self.batch_indexer,
            config=self.config
        )
        
        self.logger.info("✅ QID application initialized")
    
    def _init_components(self):
        """Initialize AI and database components."""
        self.logger.info("Initializing components...")
        
        # Encoders
        self.image_encoder = ImageEncoder(
            model_name=self.config.model_name,
            device=self.config.device
        )
        
        self.text_encoder = TextEncoder(
            model_name=self.config.model_name,
            device=self.config.device
        )
        
        # Databases
        self.vector_store = VectorStore(
            dimension=self.config.embedding_dim,
            index_type=self.config.get('database.index_type'),
            metric=self.config.get('database.metric')
        )
        
        self.metadata_store = MetadataStore(
            db_path=self.config.get('database.metadata_path')
        )
        
        # Load existing data if available
        embeddings_path = Path(self.config.get('database.embeddings_path'))
        if embeddings_path.exists():
            try:
                self.vector_store.load(str(embeddings_path))
                self.logger.info(f"Loaded {len(self.vector_store)} vectors")
            except Exception as e:
                self.logger.warning(f"Could not load vectors: {e}")
        
        # Indexer
        self.batch_indexer = BatchIndexer(
            image_encoder=self.image_encoder,
            vector_store=self.vector_store,
            metadata_store=self.metadata_store,
            batch_size=self.config.batch_size,
            config=self.config
        )
        
        # Search engine
        self.search_engine = SearchEngine(
            text_encoder=self.text_encoder,
            vector_store=self.vector_store,
            metadata_store=self.metadata_store,
            default_top_k=self.config.get('search.default_top_k')
        )
        
        self.logger.info("✅ Components initialized")
    
    def run(self):
        """Start the application."""
        self.logger.info("Starting main loop")
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Start
        self.root.mainloop()
        
        self.logger.info("Application closed")
    
    def cleanup(self):
        """Cleanup resources on exit."""
        self.logger.info("Cleaning up...")
        
        # Save vector store
        try:
            embeddings_path = self.config.get('database.embeddings_path')
            self.vector_store.save(embeddings_path)
        except Exception as e:
            self.logger.error(f"Failed to save vectors: {e}")
        
        # Close metadata store
        self.metadata_store.close()
        
        self.logger.info("Cleanup complete")


def main():
    """Entry point for the application."""
    try:
        app = QIDApp()
        app.run()
        app.cleanup()
    except Exception as e:
        messagebox.showerror("Error", f"Application failed to start:\n{e}")
        raise


if __name__ == "__main__":
    main()