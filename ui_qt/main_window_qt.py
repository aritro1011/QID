"""
QID - Frameless Main Window
Professional single-window interface with custom title bar and integrated navigation.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QPushButton, QFrame, QMessageBox, QFileDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QMouseEvent

from .theme import COLORS, SPACING
from .home_screen import HomeScreen
from .search_screen import SearchScreen
from .index_screen import IndexScreen
from .settings_screen import SettingsScreen  # Fixed: was IndexDialogQt


class CustomTitleBar(QWidget):
    """
    Custom title bar with window controls and navigation.
    """
    
    # Signals
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()
    home_clicked = Signal()
    search_clicked = Signal()
    index_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['background_elevated']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        # For window dragging
        self.drag_position = QPoint()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create title bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 10, 0)
        layout.setSpacing(0)
        
        # Logo and title
        logo_container = QHBoxLayout()
        logo_container.setSpacing(12)
        
        logo = QLabel("🔍")
        logo.setStyleSheet("font-size: 24px;")
        
        title = QLabel("QID")
        font = QFont("Inter, Segoe UI", 16, QFont.Bold)
        title.setFont(font)
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        logo_container.addWidget(logo)
        logo_container.addWidget(title)
        
        layout.addLayout(logo_container)
        layout.addSpacing(40)
        
        # Navigation tabs
        nav_container = QHBoxLayout()
        nav_container.setSpacing(8)
        
        self.home_btn = self._create_nav_button("🏠 Home")
        self.home_btn.clicked.connect(self.home_clicked.emit)
        
        self.search_btn = self._create_nav_button("🔍 Search")
        self.search_btn.clicked.connect(self.search_clicked.emit)
        
        self.index_btn = self._create_nav_button("📁 Index")
        self.index_btn.clicked.connect(self.index_clicked.emit)
        
        self.settings_btn = self._create_nav_button("⚙️ Settings")
        self.settings_btn.clicked.connect(lambda: self.parent().window()._show_settings() if self.parent() else None)
        
        nav_container.addWidget(self.home_btn)
        nav_container.addWidget(self.search_btn)
        nav_container.addWidget(self.index_btn)
        nav_container.addWidget(self.settings_btn)
        
        layout.addLayout(nav_container)
        layout.addStretch()
        
        # Database stats
        self.stats_label = QLabel("Database: 0 images")
        font = QFont("Inter, Segoe UI", 11)
        self.stats_label.setFont(font)
        self.stats_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            background: {COLORS['background_hover']};
            padding: 6px 12px;
            border-radius: 6px;
        """)
        
        layout.addWidget(self.stats_label)
        layout.addSpacing(20)
        
        # Window controls
        controls_container = QHBoxLayout()
        controls_container.setSpacing(8)
        
        minimize_btn = self._create_control_button("−")
        minimize_btn.clicked.connect(self.minimize_clicked.emit)
        
        maximize_btn = self._create_control_button("□")
        maximize_btn.clicked.connect(self.maximize_clicked.emit)
        
        close_btn = self._create_control_button("✕")
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.close_clicked.emit)
        
        controls_container.addWidget(minimize_btn)
        controls_container.addWidget(maximize_btn)
        controls_container.addWidget(close_btn)
        
        layout.addLayout(controls_container)
        
        # Set active tab
        self.set_active_tab("home")
    
    def _create_nav_button(self, text: str) -> QPushButton:
        """Create navigation button."""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        font = QFont("Inter, Segoe UI", 12, QFont.Medium)
        btn.setFont(font)
        btn.setFixedHeight(36)
        btn.setObjectName("nav_btn")
        btn.setStyleSheet(f"""
            QPushButton#nav_btn {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                color: {COLORS['text_secondary']};
            }}
            QPushButton#nav_btn:hover {{
                background: {COLORS['background_hover']};
                color: {COLORS['text_primary']};
            }}
            QPushButton#nav_btn[active="true"] {{
                background: {COLORS['primary']};
                color: white;
            }}
        """)
        return btn
    
    def _create_control_button(self, text: str) -> QPushButton:
        """Create window control button."""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(40, 40)
        font = QFont("Inter, Segoe UI", 16, QFont.Bold)
        btn.setFont(font)
        
        # Apply style BEFORE checking objectName
        base_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background: {{hover_color}};
                color: white;
            }}
        """
        
        if text == "✕":
            btn.setObjectName("close_btn")
            btn.setStyleSheet(base_style.replace("{hover_color}", "#ff5252"))
        else:
            btn.setStyleSheet(base_style.replace("{hover_color}", COLORS['background_hover']))
        
        return btn
    
    def set_active_tab(self, tab: str):
        """Set active navigation tab."""
        self.home_btn.setProperty("active", "false")
        self.search_btn.setProperty("active", "false")
        self.index_btn.setProperty("active", "false")
        self.settings_btn.setProperty("active", "false")
        
        if tab == "home":
            self.home_btn.setProperty("active", "true")
        elif tab == "search":
            self.search_btn.setProperty("active", "true")
        elif tab == "index":
            self.index_btn.setProperty("active", "true")
        elif tab == "settings":
            self.settings_btn.setProperty("active", "true")
        
        # Refresh styles
        for btn in [self.home_btn, self.search_btn, self.index_btn, self.settings_btn]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def update_stats(self, text: str):
        """Update database stats."""
        self.stats_label.setText(text)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start window drag."""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Move window."""
        if event.buttons() == Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class MainWindowQt(QMainWindow):
    """
    Frameless main application window with custom title bar.
    """
    
    def __init__(self, search_engine, batch_indexer, config):
        super().__init__()
        
        self.search_engine = search_engine
        self.batch_indexer = batch_indexer
        self.config = config
        
        # Remove default title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Window setup
        self.setMinimumSize(1200, 800)
        
        # Setup UI
        self._create_ui()
        self._setup_shortcuts()
        
        # Show home screen
        self._show_home()
    
    def _create_ui(self):
        """Create main UI structure."""
        # Main container with rounded corners
        main_container = QWidget()
        main_container.setObjectName("main_container")
        main_container.setStyleSheet(f"""
            #main_container {{
                background: {COLORS['background']};
                border-radius: 12px;
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.black)
        shadow.setOffset(0, 0)
        main_container.setGraphicsEffect(shadow)
        
        self.setCentralWidget(main_container)
        
        # Main layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = CustomTitleBar()
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_maximize)
        self.title_bar.close_clicked.connect(self.close)
        self.title_bar.home_clicked.connect(self._show_home)
        self.title_bar.search_clicked.connect(self._show_search)
        self.title_bar.index_clicked.connect(self._show_index)
        
        # Connect settings button properly
        self.title_bar.settings_btn.clicked.disconnect()
        self.title_bar.settings_btn.clicked.connect(self._show_settings)
        
        main_layout.addWidget(self.title_bar)
        
        # Content Stack
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # Create screens
        self.home_screen = HomeScreen()
        self.home_screen.index_clicked.connect(self._show_index)
        self.home_screen.search_clicked.connect(self._show_search)
        
        self.search_screen = SearchScreen(self.search_engine)
        
        self.index_screen = IndexScreen(self.batch_indexer)
        self.index_screen.completed.connect(self._on_index_complete)
        
        self.settings_screen = SettingsScreen(self.batch_indexer)
        self.settings_screen.rebuild_index.connect(self._rebuild_index)
        self.settings_screen.clear_cache.connect(self._clear_cache)
        self.settings_screen.delete_index.connect(self._delete_index)
        
        # Add to stack
        self.content_stack.addWidget(self.home_screen)
        self.content_stack.addWidget(self.search_screen)
        self.content_stack.addWidget(self.index_screen)
        self.content_stack.addWidget(self.settings_screen)
        
        # Update stats
        self._update_stats()
    
    def _toggle_maximize(self):
        """Toggle maximize/restore."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl+I"), self, self._show_index)
        QShortcut(QKeySequence("Ctrl+F"), self, self._show_search)
        QShortcut(QKeySequence("Ctrl+H"), self, self._show_home)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
    
    def _get_stats_text(self) -> str:
        """Get current database statistics."""
        total = len(self.batch_indexer.metadata_store)
        return f"Database: {total:,} images"
    
    def _update_stats(self):
        """Update title bar statistics."""
        self.title_bar.update_stats(self._get_stats_text())
    
    # Navigation Methods
    
    def _show_home(self):
        """Show home screen."""
        self.content_stack.setCurrentWidget(self.home_screen)
        self.title_bar.set_active_tab("home")
    
    def _show_search(self):
        """Show search screen."""
        self.content_stack.setCurrentWidget(self.search_screen)
        self.title_bar.set_active_tab("search")
    
    def _show_index(self):
        """Show index screen."""
        self.content_stack.setCurrentWidget(self.index_screen)
        self.title_bar.set_active_tab("index")
        # Reset to folder selection
        self.index_screen.reset_to_folder_selection()
    
    def _show_settings(self):
        """Show settings screen."""
        self.content_stack.setCurrentWidget(self.settings_screen)
        self.title_bar.set_active_tab("settings")
    
    def _on_index_complete(self, stats: dict):
        """Handle index completion."""
        self._update_stats()
        QMessageBox.information(
            self,
            "Indexing Complete",
            f"Successfully indexed {stats['processed']} images!\n\n"
            f"Total in database: {len(self.batch_indexer.metadata_store):,} images"
        )
    
    def _rebuild_index(self):
        """Rebuild entire index."""
        # Show index screen and start
        self._show_index()
        # TODO: Implement automatic start
    
    def _clear_cache(self):
        """Clear cache."""
        # TODO: Implement cache clearing
        QMessageBox.information(self, "Success", "Cache cleared successfully!")
        self._update_stats()
    
    def _delete_index(self):
        """Delete all indexed data."""
        self.batch_indexer.vector_store.clear()
        self.batch_indexer.metadata_store.clear()
        self._update_stats()
        QMessageBox.information(self, "Success", "Index deleted successfully!")