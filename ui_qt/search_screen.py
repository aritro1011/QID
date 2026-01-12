"""
QID - Search Screen
Modern search interface with results grid.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from .theme import COLORS, SPACING, RADIUS
from .image_grid_qt import ImageGridQt
from .image_viewer_qt import ImageViewerQt


class SearchBar(QWidget):
    """
    Professional search bar with gradient button.
    """
    
    search_triggered = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search your images... (e.g., 'sunset at the beach')")
        self.search_input.returnPressed.connect(self._on_search)
        
        font = QFont("Inter, Segoe UI", 14)
        self.search_input.setFont(font)
        self.search_input.setMinimumHeight(56)
        
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['background_elevated']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
                padding: 0 20px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
                background: {COLORS['background_hover']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_tertiary']};
            }}
        """)
        
        # Search button
        self.search_button = QPushButton("🔍 Search")
        self.search_button.clicked.connect(self._on_search)
        
        font = QFont("Inter, Segoe UI", 14, QFont.DemiBold)
        self.search_button.setFont(font)
        self.search_button.setMinimumSize(140, 56)
        self.search_button.setCursor(Qt.PointingHandCursor)
        
        self.search_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_start']}, 
                    stop:1 {COLORS['gradient_end']}
                );
                color: white;
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c8ef5, 
                    stop:1 #8b5cb8
                );
            }}
            QPushButton:pressed {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5563d4, 
                    stop:1 #6843a0
                );
            }}
        """)
        
        layout.addWidget(self.search_input, stretch=1)
        layout.addWidget(self.search_button)
    
    def _on_search(self):
        """Execute search."""
        query = self.search_input.text().strip()
        if query:
            self.search_triggered.emit(query)
    
    def set_query(self, query: str):
        """Set search query."""
        self.search_input.setText(query)
    
    def clear(self):
        """Clear search input."""
        self.search_input.clear()
        self.search_input.setFocus()


class SearchScreen(QWidget):
    """
    Search interface with results grid.
    """
    
    # Signals
    back_clicked = Signal()
    
    def __init__(self, search_engine, parent=None):
        super().__init__(parent)
        
        self.search_engine = search_engine
        
        self.setStyleSheet(f"background: {COLORS['background']};")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 32)
        main_layout.setSpacing(24)
        
        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(24)
        
        # Title
        title = QLabel("Search your local library with natural language")
        title.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI", 20, QFont.DemiBold)
        title.setFont(font)
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        header_layout.addWidget(title)
        
        # Search bar
        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._on_search)
        header_layout.addWidget(self.search_bar)
        
        # Example queries
        examples_layout = QHBoxLayout()
        examples_layout.setAlignment(Qt.AlignCenter)
        examples_layout.setSpacing(8)
        
        try_label = QLabel("Try:")
        font = QFont("Inter, Segoe UI", 11)
        try_label.setFont(font)
        try_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        examples_layout.addWidget(try_label)
        
        for example in ['"sunset at the beach"', '"blue vintage car"', '"family dinner outdoor"']:
            btn = QPushButton(example)
            btn.clicked.connect(lambda checked, q=example.strip('"'): self._set_example(q))
            btn.setCursor(Qt.PointingHandCursor)
            
            font = QFont("Inter, Segoe UI", 11)
            btn.setFont(font)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 6px 12px;
                    color: {COLORS['text_secondary']};
                }}
                QPushButton:hover {{
                    background: {COLORS['background_hover']};
                    color: {COLORS['text_primary']};
                }}
            """)
            
            examples_layout.addWidget(btn)
        
        header_layout.addLayout(examples_layout)
        
        main_layout.addLayout(header_layout)
        
        # Results header
        self.results_header = QWidget()
        results_header_layout = QHBoxLayout(self.results_header)
        results_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_label = QLabel("Search Results")
        font = QFont("Inter, Segoe UI", 16, QFont.DemiBold)
        self.results_label.setFont(font)
        self.results_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        self.results_count = QLabel("")
        font = QFont("Inter, Segoe UI", 13)
        self.results_count.setFont(font)
        self.results_count.setStyleSheet(f"color: {COLORS['primary']};")
        
        results_header_layout.addWidget(self.results_label)
        results_header_layout.addWidget(self.results_count)
        results_header_layout.addStretch()
        
        self.results_header.setVisible(False)
        main_layout.addWidget(self.results_header)
        
        # Image grid (scrollable)
        self.image_grid = ImageGridQt(columns=4, thumbnail_size=200)
        self.image_grid.image_clicked.connect(self._on_image_clicked)
        main_layout.addWidget(self.image_grid, stretch=1)
        
        # Image viewer
        self.image_viewer = ImageViewerQt(self)
        
        # Empty state
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_icon = QLabel("🔍")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setStyleSheet("font-size: 64px;")
        
        empty_text = QLabel("Search to find your images")
        empty_text.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI", 16)
        empty_text.setFont(font)
        empty_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        
        main_layout.addWidget(self.empty_state)
    
    def _set_example(self, query: str):
        """Set example query and search."""
        self.search_bar.set_query(query)
        self._on_search(query)
    
    def _on_search(self, query: str):
        """Execute search."""
        if not query:
            return
        
        # Hide empty state
        self.empty_state.setVisible(False)
        self.results_header.setVisible(True)
        
        # Update UI
        self.results_label.setText(f"Searching...")
        self.results_count.setText("")
        
        # Use QTimer to perform search asynchronously for better performance
        QTimer.singleShot(0, lambda: self._perform_search(query))
    
    def _perform_search(self, query: str):
        """Perform the actual search operation."""
        # Perform search with adaptive threshold
        results = self.search_engine.search(
            query,
            top_k=50,
            adaptive_threshold=True
        )
        
        # Display results
        if results:
            self.image_grid.display_results(results)
            self.results_label.setText("Search Results")
            self.results_count.setText(f"{len(results)} FOUND")
        else:
            self.image_grid.clear()
            self.results_label.setText("No Results")
            self.results_count.setText("")
    
    def clear_search(self):
        """Clear search results."""
        self.search_bar.clear()
        self.image_grid.clear()
        self.empty_state.setVisible(True)
        self.results_header.setVisible(False)
    
    def _on_image_clicked(self, result: dict, all_results: list, index: int):
        """Handle image click - show in viewer."""
        self.image_viewer.show_image(result, all_results, index)