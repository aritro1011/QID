"""
QID - Main Window (Professional, Clean)
No top nav bar - menu only.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, 
    QLabel, QStatusBar, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from .theme import COLORS, SPACING
from .home_screen import HomeScreen
from .search_screen import SearchScreen
from .index_dialog_qt import IndexDialogQt


class MainWindowQt(QMainWindow):
    """
    Main application window - Clean and professional.
    """
    
    def __init__(self, search_engine, batch_indexer, config):
        super().__init__()
        
        self.search_engine = search_engine
        self.batch_indexer = batch_indexer
        self.config = config
        
        # Window setup
        self.setWindowTitle("QID - Query Images by Description")
        self.setMinimumSize(1200, 800)
        
        # Setup UI
        self._create_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._setup_shortcuts()
        
        # Show home screen
        self._show_home()
    
    def _create_ui(self):
        """Create main UI structure."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - No nav bar!
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content Stack (different screens)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # Create screens
        self.home_screen = HomeScreen()
        self.home_screen.index_clicked.connect(self._on_index_clicked)
        self.home_screen.search_clicked.connect(self._on_search_clicked)
        
        # Search screen (real implementation!)
        self.search_screen = SearchScreen(self.search_engine)
        
        # Add to stack
        self.content_stack.addWidget(self.home_screen)
        self.content_stack.addWidget(self.search_screen)
    
    def _create_menu_bar(self):
        """Create menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Index Folder...", self._on_index_clicked)
        file_menu.addAction("Index Single Image...", self._on_index_single)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Database menu
        db_menu = menu_bar.addMenu("Database")
        db_menu.addAction("Statistics", self._show_stats)
        db_menu.addAction("Clear Database...", self._clear_database)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About", self._show_about)
        help_menu.addAction("Quick Start", self._show_quickstart)
    
    def _create_status_bar(self):
        """Create professional status bar."""
        status = QStatusBar()
        self.setStatusBar(status)
        
        # Status message
        self.status_label = QLabel("Ready")
        font = QFont("Inter, Segoe UI, sans-serif", 11)
        self.status_label.setFont(font)
        status.addWidget(self.status_label)
        
        status.addPermanentWidget(QLabel(" | "))
        
        # Database stats
        self.stats_label = QLabel(self._get_stats_text())
        font = QFont("Inter, Segoe UI, sans-serif", 11)
        self.stats_label.setFont(font)
        status.addPermanentWidget(self.stats_label)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+I: Index
        QShortcut(QKeySequence("Ctrl+I"), self, self._on_index_clicked)
        
        # Ctrl+F: Search
        QShortcut(QKeySequence("Ctrl+F"), self, self._show_search)
        
        # Ctrl+Q: Quit
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        
        # F5: Home
        QShortcut(QKeySequence("F5"), self, self._show_home)
        
        # Ctrl+S: Stats
        QShortcut(QKeySequence("Ctrl+S"), self, self._show_stats)
    def _get_stats_text(self) -> str:
        """Get current database statistics."""
        total = len(self.batch_indexer.metadata_store)
        return f"Database: {total:,} images"
    
    def _update_stats(self):
        """Update status bar statistics."""
        self.stats_label.setText(self._get_stats_text())
    
    # Navigation Methods
    
    def _show_home(self):
        """Show home screen."""
        self.content_stack.setCurrentWidget(self.home_screen)
        self.status_label.setText("Ready")
    
    def _show_search(self):
        """Show search screen."""
        self.content_stack.setCurrentWidget(self.search_screen)
        self.status_label.setText("Ready to search")
    
    # Action Methods
    
    def _on_index_clicked(self):
        """Handle index folder action."""
        dialog = IndexDialogQt(self.batch_indexer, self)
        dialog.completed.connect(self._on_index_complete)
        dialog.show_with_folder("data/images")
    
    def _on_index_complete(self, stats: dict):
        """Handle index completion."""
        self._update_stats()
        self.status_label.setText(f"Indexed {stats['processed']} images")
    
    def _on_index_single(self):
        """Handle index single image."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "data/images",
            "Images (*.jpg *.jpeg *.png *.bmp *.gif *.webp)"
        )
        
        if file:
            self.status_label.setText(f"Would index: {file}")
    
    def _on_search_clicked(self):
        """Handle search action."""
        self._show_search()
    
    def _show_stats(self):
        """Show database statistics."""
        stats = self.batch_indexer.get_stats()
        
        msg = (
            f"Database Statistics\n\n"
            f"Total Images: {stats['total_images']:,}\n"
            f"Total Vectors: {stats['total_vectors']:,}\n"
            f"Vector Dimension: {stats['vector_dimension']}\n"
            f"Index Type: {stats['index_type']}\n"
        )
        
        QMessageBox.information(self, "Statistics", msg)
    
    def _clear_database(self):
        """Clear database."""
        reply = QMessageBox.question(
            self,
            "Clear Database",
            "This will delete all indexed images!\n\n"
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Double confirm
            reply2 = QMessageBox.question(
                self,
                "Confirm",
                "Really delete everything?\n"
                "This cannot be undone!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply2 == QMessageBox.Yes:
                self.batch_indexer.vector_store.clear()
                self.batch_indexer.metadata_store.clear()
                self._update_stats()
                QMessageBox.information(self, "Success", "Database cleared")
    
    def _show_about(self):
        """Show about dialog."""
        msg = (
            "QID - Query Images by Description\n\n"
            "Version 1.0.0 (Qt)\n\n"
            "A semantic image search system powered by\n"
            "OpenAI's CLIP model.\n\n"
            "Find images using natural language!"
        )
        
        QMessageBox.about(self, "About QID", msg)
    
    def _show_quickstart(self):
        """Show quick start guide."""
        msg = (
            "Quick Start Guide\n\n"
            "1. Index Images:\n"
            "   File → Index Folder → Select folder\n\n"
            "2. Search:\n"
            "   Click 'Search My Images' card\n\n"
            "3. View Results:\n"
            "   Click any image for full size\n"
        )
        
        QMessageBox.information(self, "Quick Start", msg)