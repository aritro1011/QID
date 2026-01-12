"""
QID - Image Viewer
Beautiful lightbox for viewing images in-app with fullscreen and file location access.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPixmap, QFont, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QStyle
from pathlib import Path
import subprocess
import platform

from .theme import COLORS


class ViewerTitleBar(QWidget):
    """
    Custom title bar for image viewer with window controls only.
    """
    
    # Signals
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            ViewerTitleBar {{
                background: {COLORS['background_elevated']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        # For window dragging
        self.drag_position = QPoint()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create title bar UI with 3-cluster layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)
        
        # ---------- LEFT CLUSTER ----------
        left_cluster = QWidget()
        left_layout = QHBoxLayout(left_cluster)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.title_label = QLabel("Preview Mode")
        font = QFont("Inter, Segoe UI", 14, QFont.Bold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        
        left_layout.addWidget(self.title_label)
        left_layout.addStretch()
        
        # ---------- CENTER CLUSTER (Main buttons) ----------
        center_cluster = QWidget()
        center_layout = QHBoxLayout(center_cluster)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)
        center_layout.setAlignment(Qt.AlignCenter)
        
        # Match badge
        self.match_badge = QLabel("98.4% Match")
        font = QFont("Inter, Segoe UI", 11, QFont.Bold)
        self.match_badge.setFont(font)
        self.match_badge.setFixedHeight(36)
        self.match_badge.setStyleSheet(f"""
            background: {COLORS['success']};
            color: {COLORS['background']};
            border-radius: 8px;
            padding: 0 16px;
        """)
        
        # Navigation buttons
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.setCursor(Qt.PointingHandCursor)
        self.prev_button.setFixedHeight(36)
        font = QFont("Inter, Segoe UI", 11)
        self.prev_button.setFont(font)
        self.prev_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 0 16px;
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
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.setFixedHeight(36)
        font = QFont("Inter, Segoe UI", 11)
        self.next_button.setFont(font)
        self.next_button.setStyleSheet(self.prev_button.styleSheet())
        
        # Open File Location button
        self.location_btn = QPushButton("📁 Open File Location")
        self.location_btn.setCursor(Qt.PointingHandCursor)
        self.location_btn.setFixedHeight(36)
        font = QFont("Inter, Segoe UI", 11, QFont.Bold)
        self.location_btn.setFont(font)
        self.location_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                color: white;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        
        center_layout.addWidget(self.match_badge)
        center_layout.addWidget(self.prev_button)
        center_layout.addWidget(self.next_button)
        center_layout.addWidget(self.location_btn)
        
        # ---------- RIGHT CLUSTER (Window controls) ----------
        right_cluster = QWidget()
        right_layout = QHBoxLayout(right_cluster)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right_layout.setAlignment(Qt.AlignRight)
        
        minimize_btn = self._create_control_button("min")
        maximize_btn = self._create_control_button("max")
        close_btn = self._create_control_button("close")
        
        minimize_btn.clicked.connect(self.minimize_clicked.emit)
        maximize_btn.clicked.connect(self.maximize_clicked.emit)
        close_btn.clicked.connect(self.close_clicked.emit)
        
        right_layout.addWidget(minimize_btn)
        right_layout.addWidget(maximize_btn)
        right_layout.addWidget(close_btn)
        
        # Add all three clusters with equal width
        layout.addWidget(left_cluster, stretch=1)
        layout.addWidget(center_cluster, stretch=1)
        layout.addWidget(right_cluster, stretch=1)
    
    def _create_control_button(self, role: str) -> QPushButton:
        """Create window control button."""
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(40, 40)
        
        font = QFont("Inter, Segoe UI", 14, QFont.Bold)
        btn.setFont(font)
        
        # Assign native system icons
        if role == "min":
            btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        elif role == "max":
            btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        elif role == "close":
            btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
            btn.setObjectName("close_btn")
        
        # Styles
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


class ImageViewerQt(QDialog):
    """
    Lightbox image viewer with navigation and file location access.
    """
    
    # Signals
    next_image = Signal()
    prev_image = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_result = None
        self.all_results = []
        self.current_index = 0
        
        # Dialog setup - Frameless
        self.setWindowTitle("Image Preview")
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._create_ui()
        
        # Install event filter for keyboard
        self.installEventFilter(self)
    
    def _create_ui(self):
        """Create UI."""
        # Main container
        main_container = QWidget()
        main_container.setObjectName("viewer_container")
        main_container.setStyleSheet(f"""
            #viewer_container {{
                background: rgba(10, 14, 26, 0.98);
                border-radius: 0px;
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.black)
        shadow.setOffset(0, 0)
        main_container.setGraphicsEffect(shadow)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(main_container)
        
        # Container layout
        container_layout = QVBoxLayout(main_container)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Custom title bar
        self.title_bar = ViewerTitleBar()
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_maximize)
        self.title_bar.close_clicked.connect(self.close)
        
        # Connect existing functionality to title bar buttons
        self.title_bar.prev_button.clicked.connect(self._on_prev)
        self.title_bar.next_button.clicked.connect(self._on_next)
        self.title_bar.location_btn.clicked.connect(self._open_file_location)
        
        container_layout.addWidget(self.title_bar)
        
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
            background: transparent;
        """)
        
        image_layout.addWidget(self.image_label)
        
        container_layout.addWidget(image_container, stretch=1)
        
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
        self.filename_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        
        # Resolution
        self.resolution_label = QLabel("")
        font = QFont("Inter, Segoe UI", 11)
        self.resolution_label.setFont(font)
        self.resolution_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        
        bottom_layout.addWidget(self.filename_label)
        bottom_layout.addWidget(self.resolution_label)
        
        container_layout.addWidget(bottom_bar)
    
    def _toggle_maximize(self):
        """Toggle maximize/restore."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def show_image(self, result: dict, all_results: list = None, index: int = 0):
        """
        Display an image in fullscreen.
        
        Args:
            result: Image result dict
            all_results: All results for navigation
            index: Current index in results
        """
        self.current_result = result
        self.all_results = all_results or [result]
        self.current_index = index
        
        # Update navigation buttons
        self.title_bar.prev_button.setEnabled(index > 0)
        self.title_bar.next_button.setEnabled(index < len(self.all_results) - 1)
        
        # Load and display image
        self._load_current_image()
        
        # Show maximized
        self.showMaximized()
    
    def _load_current_image(self):
        """Load the current image into the viewer."""
        result = self.current_result
        image_path = result['file_path']
        
        if Path(image_path).exists():
            pixmap = QPixmap(image_path)
            
            if not pixmap.isNull():
                # Get available space (accounting for top/bottom bars)
                available_width = self.width() - 100 if self.width() > 100 else 1000
                available_height = self.height() - 200 if self.height() > 200 else 800
                
                # Scale to fit screen while maintaining aspect ratio
                scaled = pixmap.scaled(
                    available_width,
                    available_height,
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
                
                self.title_bar.match_badge.setText(f"{score:.1f}% Match")
                self.title_bar.match_badge.setStyleSheet(f"""
                    background: {badge_color};
                    color: {COLORS['background']};
                    border-radius: 8px;
                    padding: 0 16px;
                    font-weight: bold;
                """)
                
                # Update title
                self.title_bar.title_label.setText(f"Preview Mode • {self.current_index + 1} of {len(self.all_results)}")
            else:
                self._show_error("Failed to load image")
        else:
            self._show_error("Image file not found")
    
    def _show_error(self, message: str):
        """Show error message."""
        self.image_label.clear()
        self.image_label.setText(f"❌ {message}")
        font = QFont("Inter, Segoe UI", 16)
        self.image_label.setFont(font)
        self.image_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
    
    def _on_prev(self):
        """Show previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.current_result = self.all_results[self.current_index]
            self._load_current_image()
            # Update navigation buttons
            self.title_bar.prev_button.setEnabled(self.current_index > 0)
            self.title_bar.next_button.setEnabled(self.current_index < len(self.all_results) - 1)
    
    def _on_next(self):
        """Show next image."""
        if self.current_index < len(self.all_results) - 1:
            self.current_index += 1
            self.current_result = self.all_results[self.current_index]
            self._load_current_image()
            # Update navigation buttons
            self.title_bar.prev_button.setEnabled(self.current_index > 0)
            self.title_bar.next_button.setEnabled(self.current_index < len(self.all_results) - 1)
    
    def _open_file_location(self):
        """Open the file location in system file explorer."""
        if not self.current_result:
            return
        
        file_path = Path(self.current_result['file_path'])
        
        if not file_path.exists():
            return
        
        # Get the directory
        directory = file_path.parent
        
        # Open in file explorer based on OS
        system = platform.system()
        
        try:
            if system == "Windows":
                # Windows: open Explorer and select the file
                subprocess.run(['explorer', '/select,', str(file_path)])
            elif system == "Darwin":  # macOS
                # macOS: open Finder and select the file
                subprocess.run(['open', '-R', str(file_path)])
            else:  # Linux
                # Linux: just open the directory
                subprocess.run(['xdg-open', str(directory)])
        except Exception as e:
            print(f"Failed to open file location: {e}")
    
    def resizeEvent(self, event):
        """Handle window resize - reload image to fit new size."""
        super().resizeEvent(event)
        if self.current_result:
            # Reload image with new dimensions
            self._load_current_image()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key = event.key()
        
        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Left:
            self._on_prev()
        elif key == Qt.Key_Right:
            self._on_next()
        elif key == Qt.Key_Space:
            self._on_next()
        else:
            super().keyPressEvent(event)