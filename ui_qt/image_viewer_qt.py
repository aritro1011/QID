"""
QID - Image Viewer
Beautiful lightbox for viewing images in-app.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QKeyEvent
from pathlib import Path

from .theme import COLORS


class ImageViewerQt(QDialog):
    """
    Lightbox image viewer with navigation.
    """
    
    # Signals
    next_image = Signal()
    prev_image = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_result = None
        self.all_results = []
        self.current_index = 0
        
        # Dialog setup
        self.setWindowTitle("Image Preview")
        self.setModal(True)
        self.showMaximized()
        
        # Dark background
        self.setStyleSheet(f"""
            QDialog {{
                background: rgba(10, 14, 26, 0.95);
            }}
        """)
        
        self._create_ui()
        
        # Install event filter for keyboard
        self.installEventFilter(self)
    
    def _create_ui(self):
        """Create UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 0, 24, 0)
        
        # Title
        self.title_label = QLabel("Preview Mode")
        font = QFont("Inter, Segoe UI", 14, QFont.Bold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        
        # Match badge
        self.match_badge = QLabel("98.4% Match")
        font = QFont("Inter, Segoe UI", 12, QFont.Bold)
        self.match_badge.setFont(font)
        self.match_badge.setStyleSheet(f"""
            background: {COLORS['success']};
            color: {COLORS['background']};
            border-radius: 16px;
            padding: 6px 16px;
        """)
        
        top_layout.addWidget(self.match_badge)
        
        # Navigation buttons
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.clicked.connect(self._on_prev)
        self.prev_button.setCursor(Qt.PointingHandCursor)
        font = QFont("Inter, Segoe UI", 11)
        self.prev_button.setFont(font)
        self.prev_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 16px;
                color: {COLORS['text_secondary']};
            }}
            QPushButton:hover {{
                background: {COLORS['background_hover']};
                color: {COLORS['text_primary']};
            }}
            QPushButton:disabled {{
                color: {COLORS['text_tertiary']};
                border-color: {COLORS['text_tertiary']};
            }}
        """)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self._on_next)
        self.next_button.setCursor(Qt.PointingHandCursor)
        font = QFont("Inter, Segoe UI", 11)
        self.next_button.setFont(font)
        self.next_button.setStyleSheet(self.prev_button.styleSheet())
        
        top_layout.addWidget(self.prev_button)
        top_layout.addWidget(self.next_button)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(40, 40)
        font = QFont("Inter, Segoe UI", 16)
        close_btn.setFont(font)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_secondary']};
                border-radius: 20px;
            }}
            QPushButton:hover {{
                background: {COLORS['background_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        
        top_layout.addWidget(close_btn)
        
        layout.addWidget(top_bar)
        
        # Image display area (center)
        image_container = QFrame()
        image_container.setStyleSheet("background: transparent;")
        
        image_layout = QVBoxLayout(image_container)
        image_layout.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 8px;
        """)
        
        image_layout.addWidget(self.image_label)
        
        layout.addWidget(image_container, stretch=1)
        
        # Bottom info bar
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(80)
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        
        bottom_layout = QVBoxLayout(bottom_bar)
        bottom_layout.setAlignment(Qt.AlignCenter)
        bottom_layout.setSpacing(4)
        
        # Filename
        self.filename_label = QLabel("")
        font = QFont("Inter, Segoe UI", 13, QFont.Bold)
        self.filename_label.setFont(font)
        self.filename_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        # Resolution
        self.resolution_label = QLabel("")
        font = QFont("Inter, Segoe UI", 11)
        self.resolution_label.setFont(font)
        self.resolution_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        bottom_layout.addWidget(self.filename_label)
        bottom_layout.addWidget(self.resolution_label)
        
        layout.addWidget(bottom_bar)
    
    def show_image(self, result: dict, all_results: list = None, index: int = 0):
        """
        Display an image.
        
        Args:
            result: Image result dict
            all_results: All results for navigation
            index: Current index in results
        """
        self.current_result = result
        self.all_results = all_results or [result]
        self.current_index = index
        
        # Update navigation buttons
        self.prev_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < len(self.all_results) - 1)
        
        # Load image
        image_path = result['file_path']
        
        if Path(image_path).exists():
            pixmap = QPixmap(image_path)
            
            if not pixmap.isNull():
                # Scale to fit screen (leave margins)
                max_width = self.width() - 200
                max_height = self.height() - 200
                
                scaled = pixmap.scaled(
                    max_width, max_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled)
                
                # Update info
                self.filename_label.setText(result['file_name'])
                self.resolution_label.setText(f"{pixmap.width()} × {pixmap.height()} px")
                
                # Update match badge
                score = result['score'] * 100
                if score >= 80:
                    badge_color = COLORS['success']
                elif score >= 60:
                    badge_color = "#ffa726"
                else:
                    badge_color = COLORS['text_secondary']
                
                self.match_badge.setText(f"{score:.1f}% Match")
                self.match_badge.setStyleSheet(f"""
                    background: {badge_color};
                    color: {COLORS['background']};
                    border-radius: 16px;
                    padding: 6px 16px;
                    font-weight: bold;
                """)
                
                # Update title
                self.title_label.setText(f"Preview Mode • {index + 1} of {len(self.all_results)}")
            else:
                self._show_error("Failed to load image")
        else:
            self._show_error("Image file not found")
        
        self.show()
    
    def _show_error(self, message: str):
        """Show error message."""
        self.image_label.clear()
        self.image_label.setText(f"❌ {message}")
        font = QFont("Inter, Segoe UI", 16)
        self.image_label.setFont(font)
        self.image_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
    
    def _on_prev(self):
        """Show previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image(
                self.all_results[self.current_index],
                self.all_results,
                self.current_index
            )
    
    def _on_next(self):
        """Show next image."""
        if self.current_index < len(self.all_results) - 1:
            self.current_index += 1
            self.show_image(
                self.all_results[self.current_index],
                self.all_results,
                self.current_index
            )
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key = event.key()
        
        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Left:
            self._on_prev()
        elif key == Qt.Key_Right:
            self._on_next()
        else:
            super().keyPressEvent(event)