"""
QID - Image Grid (Qt)
Professional grid with cards and match percentages.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QFont, QCursor
from pathlib import Path


class ImageCard(QFrame):
    """
    Professional image card with hover effect.
    """
    
    clicked = Signal(dict, list, int)  # Emits (result, all_results, index)
    
    def __init__(self, result: dict, thumbnail_size: int, index: int, parent=None):
        super().__init__(parent)
        
        self.result = result
        self.index = index
        
        self.setObjectName("image_card")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(thumbnail_size + 24, thumbnail_size + 90)
        
        # Card styling
        self.setStyleSheet(f"""
            #image_card {{
                background: rgba(21, 27, 45, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }}
            #image_card:hover {{
                background: rgba(21, 27, 45, 0.85);
                border-color: rgba(79, 108, 255, 0.4);
            }}
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        
        # Image container
        image_container = QLabel()
        image_container.setFixedSize(thumbnail_size, thumbnail_size)
        image_container.setAlignment(Qt.AlignCenter)
        image_container.setStyleSheet("""
            background: rgba(10, 14, 26, 0.5);
            border-radius: 8px;
        """)
        
        # Load and display image
        image_path = result['file_path']
        if Path(image_path).exists():
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale maintaining aspect ratio
                scaled = pixmap.scaled(
                    thumbnail_size, thumbnail_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                image_container.setPixmap(scaled)
            else:
                image_container.setText("❌")
                image_container.setStyleSheet("""
                    background: rgba(10, 14, 26, 0.5);
                    border-radius: 8px;
                    color: #ff5252;
                    font-size: 32px;
                """)
        else:
            image_container.setText("🚫")
            image_container.setStyleSheet("""
                background: rgba(10, 14, 26, 0.5);
                border-radius: 8px;
                color: #ffa726;
                font-size: 32px;
            """)
        
        layout.addWidget(image_container)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Filename
        filename = QLabel(result['file_name'])
        filename.setWordWrap(True)
        filename.setMaximumWidth(thumbnail_size)
        font = QFont("Inter, Segoe UI", 11)
        filename.setFont(font)
        filename.setStyleSheet("color: #ffffff;")
        
        # Match percentage with badge
        score = result['score'] * 100
        
        # Color based on score
        if score >= 80:
            badge_color = "#00ff94"  # Green
        elif score >= 60:
            badge_color = "#ffa726"  # Orange
        else:
            badge_color = "#8b92a8"  # Gray
        
        match_label = QLabel(f"● {score:.0f}% Match")
        font = QFont("Inter, Segoe UI", 11, QFont.Bold)
        match_label.setFont(font)
        match_label.setStyleSheet(f"color: {badge_color};")
        
        info_layout.addWidget(filename)
        info_layout.addWidget(match_label)
        
        layout.addLayout(info_layout)
    
    def mousePressEvent(self, event):
        """Handle click."""
        if event.button() == Qt.LeftButton:
            # Emit result, all_results, and index for viewer
            self.clicked.emit(self.result, [], self.index)
        super().mousePressEvent(event)


class ImageGridQt(QWidget):
    """
    Scrollable grid of image cards.
    """
    
    # Signal for image click with navigation support
    image_clicked = Signal(dict, list, int)  # result, all_results, index
    
    def __init__(self, columns: int = 4, thumbnail_size: int = 200, parent=None):
        super().__init__(parent)
        
        self.columns = columns
        self.thumbnail_size = thumbnail_size
        self.results = []
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        # Grid container
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        self.scroll_area.setWidget(self.grid_widget)
        main_layout.addWidget(self.scroll_area)
    
    def display_results(self, results: list):
        """
        Display search results in grid.
        """
        # Clear existing
        self.clear()
        
        self.results = results
        
        # Add cards to grid
        for i, result in enumerate(results):
            row = i // self.columns
            col = i % self.columns
            
            card = ImageCard(result, self.thumbnail_size, i)
            card.clicked.connect(self._on_image_clicked)
            
            self.grid_layout.addWidget(card, row, col)
        
        # Scroll to top
        self.scroll_area.verticalScrollBar().setValue(0)
    
    def _on_image_clicked(self, result: dict, all_results: list, index: int):
        """
        Handle image click - emit with all results for navigation.
        """
        # Emit with full results list for navigation
        self.image_clicked.emit(result, self.results, index)
    
    def clear(self):
        """Clear all cards."""
        # Remove all widgets from grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.results = []