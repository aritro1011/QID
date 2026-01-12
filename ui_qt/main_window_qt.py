"""
QID - Frameless Main Window
Professional single-window interface with custom title bar and integrated navigation.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QPushButton, QFrame, QMessageBox, QFileDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint, Signal, QSize
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QMouseEvent

from .theme import COLORS, SPACING
from .home_screen import HomeScreen
from .search_screen import SearchScreen
from .index_screen import IndexScreen
from .settings_screen import SettingsScreen
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QStyle

from PySide6.QtWidgets import QGraphicsOpacityEffect, QSizePolicy
from PySide6.QtCore import QPropertyAnimation


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
            CustomTitleBar {{
                background: {COLORS['background_elevated']};
                border-bottom: 1px solid {COLORS['border']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        
        # For window dragging
        self.drag_position = QPoint()
        
        self._create_ui()
        from .theme import get_stylesheet

    def _create_ui(self):
        """Create title bar UI with perfectly centered stats label."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)

        # ---------- LEFT CLUSTER ----------
        left_container = QHBoxLayout()
        left_container.setSpacing(10)

        logo = QLabel()
        root = Path(__file__).resolve().parents[1]
        logo_path = root / "assets" / "logo.png"
        pix = QPixmap(str(logo_path))
        TARGET_HEIGHT = 36
        if not pix.isNull():
            pix = pix.scaledToHeight(TARGET_HEIGHT, Qt.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("QID")
        logo.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        logo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        logo.setStyleSheet("background: transparent; border: none;")
        left_container.addWidget(logo)

        # Nav buttons
        self.home_btn = self._create_nav_button("🏠 Home")
        self.search_btn = self._create_nav_button("🔍 Search")
        self.index_btn = self._create_nav_button("📁 Index")
        self.settings_btn = self._create_nav_button("⚙️ Settings")
        self.home_btn.clicked.connect(self.home_clicked.emit)
        self.search_btn.clicked.connect(self.search_clicked.emit)
        self.index_btn.clicked.connect(self.index_clicked.emit)

        for btn in [self.home_btn, self.search_btn, self.index_btn, self.settings_btn]:
            left_container.addWidget(btn)

        left_widget = QWidget()
        left_widget.setLayout(left_container)
        left_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # ---------- RIGHT CLUSTER ----------
        right_container = QHBoxLayout()
        right_container.setSpacing(6)
        right_container.setAlignment(Qt.AlignRight)

        minimize_btn = self._create_control_button("min")
        maximize_btn = self._create_control_button("max")
        close_btn = self._create_control_button("close")
        minimize_btn.clicked.connect(self.minimize_clicked.emit)
        maximize_btn.clicked.connect(self.maximize_clicked.emit)
        close_btn.clicked.connect(self.close_clicked.emit)

        for btn in [minimize_btn, maximize_btn, close_btn]:
            right_container.addWidget(btn)

        right_widget = QWidget()
        right_widget.setLayout(right_container)
        
        # MATCH WIDTH OF LEFT CLUSTER
        right_widget.setFixedWidth(left_widget.sizeHint().width())

        # ---------- CENTER STATS ----------
        self.stats_label = QLabel("Database: 0 images")
        font = QFont("Inter, Segoe UI", 11)
        self.stats_label.setFont(font)
        self.stats_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            background: transparent;
            padding: 0;
            border: none;
        """)
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # ---------- MAIN LAYOUT ----------
        layout.addWidget(left_widget)
        layout.addStretch()
        layout.addWidget(self.stats_label)
        layout.addStretch()
        layout.addWidget(right_widget)

    def update_for_maximized(self, is_maximized: bool):
        """Update title bar styling for maximized state."""
        if is_maximized:
            self.setStyleSheet(f"""
                CustomTitleBar {{
                    background: {COLORS['background_elevated']};
                    border-bottom: 1px solid {COLORS['border']};
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                CustomTitleBar {{
                    background: {COLORS['background_elevated']};
                    border-bottom: 1px solid {COLORS['border']};
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
                }}
            """)

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
    
    def _create_control_button(self, role: str) -> QPushButton:
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(40, 40)

        font = QFont("Inter, Segoe UI", 14, QFont.Bold)
        btn.setFont(font)

        if role == "min":
            btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        elif role == "max":
            btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        elif role == "close":
            btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
            btn.setObjectName("close_btn")

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

        if role == "close":
            btn.setStyleSheet(base_style.replace("{hover_color}", "#ff4d4f"))
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
        
        for btn in [self.home_btn, self.search_btn, self.index_btn, self.settings_btn]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def update_stats(self, text: str):
        self.stats_label.setText(text)

        effect = QGraphicsOpacityEffect()
        self.stats_label.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(350)
        anim.setStartValue(0.3)
        anim.setEndValue(1.0)
        anim.start()
    
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
        
        self.is_maximized = False
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setMinimumSize(1200, 800)
        
        self._create_ui()
        self._setup_shortcuts()
        
        self._show_home()
    
    def _create_ui(self):
        """Create main UI structure."""
        self.main_container = QWidget()
        self.main_container.setObjectName("main_container")
        self.main_container.setStyleSheet(f"""
            #main_container {{
                background: {COLORS['background']};
                border-radius: 12px;
            }}
        """)
        
        self.setCentralWidget(self.main_container)
        
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar()
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_maximize)
        self.title_bar.close_clicked.connect(self.close)
        self.title_bar.home_clicked.connect(self._show_home)
        self.title_bar.search_clicked.connect(self._show_search)
        self.title_bar.index_clicked.connect(self._show_index)
        self.title_bar.settings_btn.clicked.connect(self._show_settings)
        
        main_layout.addWidget(self.title_bar)
        
        self.content_container = QWidget()
        self.content_container.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['background']};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        main_layout.addWidget(self.content_container)
        
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
        
        self.content_stack.addWidget(self.home_screen)
        self.content_stack.addWidget(self.search_screen)
        self.content_stack.addWidget(self.index_screen)
        self.content_stack.addWidget(self.settings_screen)
        
        self._update_stats()
    
    def _toggle_maximize(self):
        """Toggle maximize/restore."""
        if self.isMaximized():
            self.showNormal()
            self.is_maximized = False
        else:
            self.showMaximized()
            self.is_maximized = True
        
        self._update_container_style()
    
    def _update_container_style(self):
        """Update container styling based on window state."""
        if self.is_maximized:
            self.main_container.setStyleSheet(f"""
                #main_container {{
                    background: {COLORS['background']};
                    border-radius: 0px;
                }}
            """)
            self.content_container.setStyleSheet(f"""
                QWidget {{
                    background: {COLORS['background']};
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }}
            """)
            self.title_bar.update_for_maximized(True)
        else:
            self.main_container.setStyleSheet(f"""
                #main_container {{
                    background: {COLORS['background']};
                    border-radius: 12px;
                }}
            """)
            self.content_container.setStyleSheet(f"""
                QWidget {{
                    background: {COLORS['background']};
                    border-bottom-left-radius: 12px;
                    border-bottom-right-radius: 12px;
                }}
            """)
            self.title_bar.update_for_maximized(False)
    
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
        self._show_index()
    
    def _clear_cache(self):
        """Clear cache."""
        QMessageBox.information(self, "Success", "Cache cleared successfully!")
        self._update_stats()
    
    def _delete_index(self):
        """Delete all indexed data."""
        self.batch_indexer.vector_store.clear()
        self.batch_indexer.metadata_store.clear()
        self._update_stats()
        QMessageBox.information(self, "Success", "Index deleted successfully!")