"""
QID - Index Progress Dialog
Beautiful indexing experience with live statistics.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QFrame,
    QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import time

from .theme import COLORS, SPACING, RADIUS


class IndexWorker(QThread):
    """
    Background thread for indexing.
    """
    
    # Signals
    progress = Signal(int, int)  # current, total
    status = Signal(str)  # status message
    log = Signal(str)  # log message
    finished = Signal(dict)  # stats
    error = Signal(str)
    
    def __init__(self, batch_indexer, folder, options):
        super().__init__()
        self.batch_indexer = batch_indexer
        self.folder = folder
        self.options = options
    
    def run(self):
        """Run indexing in background."""
        try:
            self.status.emit("Starting indexing...")
            
            # Index with callbacks
            stats = self.batch_indexer.index_directory(
                self.folder,
                recursive=self.options.get('recursive', True),
                validate=self.options.get('validate', True),
                skip_existing=self.options.get('skip_existing', True)
            )
            
            self.finished.emit(stats)
            
        except Exception as e:
            self.error.emit(str(e))


class StatCard(QFrame):
    """
    Statistics card with icon and value.
    """
    
    def __init__(self, icon: str, label: str, value: str = "0", parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 32px;")
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI", 24, QFont.Bold)
        self.value_label.setFont(font)
        self.value_label.setStyleSheet(f"color: {COLORS['primary']};")
        
        # Label
        label_text = QLabel(label)
        label_text.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI", 11)
        label_text.setFont(font)
        label_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        layout.addWidget(icon_label)
        layout.addWidget(self.value_label)
        layout.addWidget(label_text)
    
    def set_value(self, value: str):
        """Update value."""
        self.value_label.setText(value)


class IndexDialogQt(QDialog):
    """
    Professional index dialog with live progress.
    """
    
    completed = Signal(dict)
    
    def __init__(self, batch_indexer, parent=None):
        super().__init__(parent)
        
        self.batch_indexer = batch_indexer
        self.worker = None
        self.start_time = None
        
        # Dialog setup
        self.setWindowTitle("Image Indexing")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        
        # Style
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['background']};
            }}
        """)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Header
        header = QLabel("Image Indexing")
        font = QFont("Inter, Segoe UI", 20, QFont.Bold)
        header.setFont(font)
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        subtitle = QLabel("Extracting AI features and indexing metadata from your local repository")
        font = QFont("Inter, Segoe UI", 12)
        subtitle.setFont(font)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        subtitle.setWordWrap(True)
        
        layout.addWidget(header)
        layout.addWidget(subtitle)
        
        # Source selection
        source_frame = QFrame()
        source_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        source_layout = QHBoxLayout(source_frame)
        
        source_label = QLabel("📁 SOURCE")
        font = QFont("Inter, Segoe UI", 10, QFont.Bold)
        source_label.setFont(font)
        source_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        
        self.folder_label = QLabel("No folder selected")
        font = QFont("Inter, Segoe UI", 11)
        self.folder_label.setFont(font)
        self.folder_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        browse_btn = QPushButton("Change Folder")
        browse_btn.clicked.connect(self._browse_folder)
        font = QFont("Inter, Segoe UI", 11)
        browse_btn.setFont(font)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
                color: {COLORS['text_secondary']};
            }}
            QPushButton:hover {{
                background: {COLORS['background_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.folder_label, stretch=1)
        source_layout.addWidget(browse_btn)
        
        layout.addWidget(source_frame)
        
        # Progress section
        progress_label = QLabel("📊 CURRENT PROGRESS")
        font = QFont("Inter, Segoe UI", 10, QFont.Bold)
        progress_label.setFont(font)
        progress_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        
        layout.addWidget(progress_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['background_elevated']};
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_start']}, 
                    stop:1 {COLORS['gradient_end']}
                );
                border-radius: 6px;
            }}
        """)
        
        layout.addWidget(self.progress_bar)
        
        # Progress text
        self.progress_text = QLabel("Ready to index")
        font = QFont("Inter, Segoe UI", 11)
        self.progress_text.setFont(font)
        self.progress_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        layout.addWidget(self.progress_text)
        
        # Statistics cards
        stats_label = QLabel("📈 LIVE STATISTICS")
        font = QFont("Inter, Segoe UI", 10, QFont.Bold)
        stats_label.setFont(font)
        stats_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        
        layout.addWidget(stats_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.total_card = StatCard("📊", "Total Indexed", "0")
        self.added_card = StatCard("➕", "Added This Session", "0")
        self.skipped_card = StatCard("⏭️", "Duplicates Skipped", "0")
        
        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.added_card)
        stats_layout.addWidget(self.skipped_card)
        
        layout.addLayout(stats_layout)
        
        # Time elapsed
        self.time_label = QLabel("⏱️  Time Elapsed: 00:00:00")
        font = QFont("Inter, Segoe UI", 11)
        self.time_label.setFont(font)
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        layout.addWidget(self.time_label)
        
        # Background indexing notice
        notice_frame = QFrame()
        notice_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(79, 108, 255, 0.1);
                border: 1px solid rgba(79, 108, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        
        notice_layout = QHBoxLayout(notice_frame)
        notice_layout.setSpacing(12)
        
        notice_icon = QLabel("ℹ️")
        notice_icon.setStyleSheet("font-size: 20px;")
        
        notice_text = QLabel("Background Indexing")
        font = QFont("Inter, Segoe UI", 11, QFont.Bold)
        notice_text.setFont(font)
        notice_text.setStyleSheet(f"color: {COLORS['primary']};")
        
        notice_desc = QLabel("You can continue browsing while indexing is in progress.")
        font = QFont("Inter, Segoe UI", 10)
        notice_desc.setFont(font)
        notice_desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        notice_layout.addWidget(notice_icon)
        notice_content = QVBoxLayout()
        notice_content.setSpacing(4)
        notice_content.addWidget(notice_text)
        notice_content.addWidget(notice_desc)
        notice_layout.addLayout(notice_content, stretch=1)
        
        layout.addWidget(notice_frame)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.start_button = QPushButton("Start Indexing")
        self.start_button.clicked.connect(self._start_indexing)
        font = QFont("Inter, Segoe UI", 13, QFont.DemiBold)
        self.start_button.setFont(font)
        self.start_button.setMinimumHeight(48)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_start']}, 
                    stop:1 {COLORS['gradient_end']}
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 32px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c8ef5, 
                    stop:1 #8b5cb8
                );
            }}
            QPushButton:disabled {{
                background: {COLORS['background_hover']};
                color: {COLORS['text_tertiary']};
            }}
        """)
        
        self.cancel_button = QPushButton("Close")
        self.cancel_button.clicked.connect(self.reject)
        font = QFont("Inter, Segoe UI", 13)
        self.cancel_button.setFont(font)
        self.cancel_button.setMinimumHeight(48)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                color: {COLORS['text_secondary']};
                padding: 0 32px;
            }}
            QPushButton:hover {{
                background: {COLORS['background_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        
        button_layout.addWidget(self.start_button, stretch=1)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _browse_folder(self):
        """Browse for folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Image Folder",
            "data/images"
        )
        
        if folder:
            self.folder_label.setText(folder)
            self.folder = folder
    
    def _start_indexing(self):
        """Start indexing process."""
        if not hasattr(self, 'folder'):
            self.folder_label.setText("Please select a folder first")
            return
        
        # Disable start button
        self.start_button.setEnabled(False)
        self.start_button.setText("Indexing...")
        
        # Start timer
        self.start_time = time.time()
        self.timer = self.startTimer(1000)  # Update every second
        
        # Create worker
        options = {
            'recursive': True,
            'validate': True,
            'skip_existing': True
        }
        
        self.worker = IndexWorker(self.batch_indexer, self.folder, options)
        self.worker.status.connect(self._update_status)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        
        # Start
        self.worker.start()
    
    def _update_status(self, message: str):
        """Update status message."""
        self.progress_text.setText(message)
    
    def _on_finished(self, stats: dict):
        """Handle completion."""
        # Stop timer
        if hasattr(self, 'timer'):
            self.killTimer(self.timer)
        
        # Update UI
        self.progress_bar.setValue(100)
        self.progress_text.setText("✅ Indexing complete!")
        
        # Update stats
        self.total_card.set_value(f"{stats['found']:,}")
        self.added_card.set_value(f"{stats['processed']:,}")
        self.skipped_card.set_value(f"{stats['found'] - stats['new']:,}")
        
        # Change button
        self.start_button.setEnabled(False)
        self.cancel_button.setText("Done")
        
        # Emit signal
        self.completed.emit(stats)
    
    def _on_error(self, error: str):
        """Handle error."""
        if hasattr(self, 'timer'):
            self.killTimer(self.timer)
        
        self.progress_text.setText(f"❌ Error: {error}")
        self.start_button.setEnabled(True)
        self.start_button.setText("Retry")
    
    def timerEvent(self, event):
        """Update elapsed time."""
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            self.time_label.setText(f"⏱️  Time Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def show_with_folder(self, folder: str = None):
        """Show dialog with pre-selected folder."""
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)
        
        self.show()