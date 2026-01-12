"""
QID - Modern Qt Application
Beautiful, animated interface with PySide6.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    ImageEncoder, TextEncoder,
    VectorStore, MetadataStore,
    BatchIndexer, SearchEngine,
    get_config, setup_logging, get_logger
)

from ui_qt.main_window_qt import MainWindowQt
from ui_qt.theme import get_stylesheet


class QIDAppQt:
    """
    QID Application with modern Qt interface.
    
    This is the new PySide6 version running alongside
    the original Tkinter app for incremental migration.
    """
    
    def __init__(self):
        """Initialize the Qt application."""
        # Create Qt Application
        self.app = QApplication(sys.argv)
        
        # Set application metadata
        self.app.setApplicationName("QID")
        self.app.setOrganizationName("QID Intelligence")
        self.app.setApplicationDisplayName("QID - Query Images by Description")
        
        # Set application icon with proper scaling
        icon_path = Path(__file__).parent / "assets" / "logo.png"
        if icon_path.exists():
            # Load the original image
            original = QPixmap(str(icon_path))
            
            if not original.isNull():
                # Create icon
                icon = QIcon()
                
                # Define target sizes for different contexts
                sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]
                
                for size in sizes:
                    # Calculate the scaling to maintain aspect ratio
                    # and fit within a square of 'size'
                    scaled = original.scaled(
                        size, size,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    
                    # Create a square pixmap with transparent background
                    square = QPixmap(size, size)
                    square.fill(Qt.transparent)
                    
                    # Center the scaled image in the square
                    from PySide6.QtGui import QPainter
                    painter = QPainter(square)
                    x = (size - scaled.width()) // 2
                    y = (size - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    painter.end()
                    
                    icon.addPixmap(square)
                
                # Set as application icon (taskbar icon)
                self.app.setWindowIcon(icon)
                
                # Store for later use
                self.app_icon = icon
            else:
                self.app_icon = None
        else:
            self.app_icon = None
        
        # Load configuration
        self.config = get_config()
        
        # Setup logging (no console spam)
        setup_logging(
            log_file=self.config.get('logging.file'),
            level=self.config.get('logging.level'),
            console=False
        )
        
        self.logger = get_logger(__name__)
        self.logger.info("🚀 Starting QID Qt application")
        
        # Apply dark theme
        self._setup_theme()
        
        # Initialize AI components (same as Tkinter version)
        self._init_components()
        
        # Create main window
        self.main_window = MainWindowQt(
            search_engine=self.search_engine,
            batch_indexer=self.batch_indexer,
            config=self.config
        )
        
        # Set window icon for taskbar appearance
        if self.app_icon:
            self.main_window.setWindowIcon(self.app_icon)
            
            # Also set on the QApplication again to ensure it's picked up
            # by the taskbar (Windows sometimes needs this)
            
            if sys.platform == 'win32':
                # On Windows, we need to set the app user model ID
                try:
                    import ctypes
                    myappid = 'qid.intelligence.imagequery.1.0'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                except:
                    pass
        
        self.logger.info("✅ QID Qt application initialized")
    
    def _setup_theme(self):
        """Apply modern dark theme."""
        # Set global stylesheet
        self.app.setStyleSheet(get_stylesheet())
        
        # Set default font
        font = QFont("Inter, Segoe UI", 10)
        font.setHintingPreference(QFont.PreferNoHinting)
        self.app.setFont(font)
        
        # High DPI is automatic in Qt6, no need to set attributes
    
    def _init_components(self):
        """Initialize AI and database components."""
        self.logger.info("Initializing AI components...")
        
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
                self.logger.info(f"📂 Loaded {len(self.vector_store)} vectors")
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
        # Show main window
        self.main_window.show()
        
        self.logger.info("🎨 Application running")
        
        # Start event loop
        return self.app.exec()
    
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
        
        self.logger.info("👋 Cleanup complete")


def main():
    """Entry point for Qt version."""
    try:
        app = QIDAppQt()
        exit_code = app.run()
        app.cleanup()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()