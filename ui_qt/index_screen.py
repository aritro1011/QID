"""
QID - Index Screen
Full-page indexing interface with live progress and stats.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QFileDialog, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
import time
from pathlib import Path

from .theme import COLORS, SPACING, RADIUS


class IndexWorker(QThread):
    """Background thread for indexing with proper progress tracking."""
    
    progress = Signal(int, int)  # current, total
    status = Signal(str)
    log = Signal(str)
    stats_update = Signal(dict)  # Real-time stats
    speed = Signal(float)  # images per second
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, batch_indexer, folder, options):
        super().__init__()
        self.batch_indexer = batch_indexer
        self.folder = folder
        self.options = options
        self.start_time = None
        self.last_speed_update = None
        self.last_speed_count = 0
        
        # Stats tracking
        self.stats = {
            'found': 0,
            'processed': 0,
            'new': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def run(self):
        """Run indexing in background with live updates."""
        try:
            self.start_time = time.time()
            self.last_speed_update = self.start_time
            
            self.status.emit("Scanning for images...")
            self.log.emit("🔍 Scanning for images...")
            
            # Find all images
            image_paths = self._find_images()
            
            if not image_paths:
                self.log.emit("⚠️ No images found in directory")
                self.finished.emit(self.stats)
                return
            
            self.stats['found'] = len(image_paths)
            self.log.emit(f"📊 Found {len(image_paths)} images")
            self.stats_update.emit(self.stats.copy())
            
            # Check which are already indexed
            self.status.emit("Checking for existing images...")
            self.log.emit("🔍 Checking for already indexed images...")
            
            if self.options.get('skip_existing', True):
                images_to_process = []
                for path in image_paths:
                    if not self.batch_indexer.metadata_store.exists(str(path.absolute())):
                        images_to_process.append(path)
                    else:
                        self.stats['skipped'] += 1
                
                self.stats['new'] = len(images_to_process)
                self.log.emit(f"⏭️ Skipping {self.stats['skipped']} already indexed images")
                self.log.emit(f"🆕 Processing {len(images_to_process)} new images")
            else:
                images_to_process = image_paths
                self.stats['new'] = len(images_to_process)
            
            self.stats_update.emit(self.stats.copy())
            
            if not images_to_process:
                self.log.emit("✅ All images already indexed!")
                self.finished.emit(self.stats)
                return
            
            # Process images in batches
            self.status.emit("Processing images...")
            self._process_images(images_to_process)
            
            # Final update
            self.log.emit(f"✅ Indexing complete! Processed {self.stats['processed']} images")
            self.finished.emit(self.stats)
            
        except Exception as e:
            import traceback
            self.log.emit(f"❌ Error: {str(e)}")
            self.log.emit(traceback.format_exc())
            self.error.emit(str(e))
    
    def _find_images(self):
        """Find all image files in directory."""
        folder = Path(self.folder)
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        
        image_paths = []
        
        if self.options.get('recursive', True):
            for ext in extensions:
                image_paths.extend(folder.rglob(f"*{ext}"))
                image_paths.extend(folder.rglob(f"*{ext.upper()}"))
        else:
            for ext in extensions:
                image_paths.extend(folder.glob(f"*{ext}"))
                image_paths.extend(folder.glob(f"*{ext.upper()}"))
        
        return sorted(set(image_paths))
    
    def _process_images(self, image_paths):
        """Process images in batches with live progress updates."""
        total = len(image_paths)
        batch_size = self.batch_indexer.batch_size
        
        for i in range(0, total, batch_size):
            batch = image_paths[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            self.status.emit(f"Processing batch {batch_num}/{total_batches}...")
            
            try:
                # Encode images
                embeddings = self.batch_indexer.image_encoder.encode_batch(
                    [str(p) for p in batch],
                    batch_size=len(batch),
                    show_progress=False
                )
                
                # Add to vector store
                vector_ids = self.batch_indexer.vector_store.add(embeddings)
                
                # Add metadata
                batch_processed = 0
                for vector_id, path in zip(vector_ids, batch):
                    success = self.batch_indexer.metadata_store.add(
                        vector_id=vector_id,
                        file_path=str(path.absolute())
                    )
                    if success:
                        batch_processed += 1
                        self.stats['processed'] += 1
                
                # Update progress
                current_total = min(i + len(batch), total)
                self.progress.emit(current_total, total)
                
                # Update speed
                self._update_speed()
                
                # Update stats
                self.stats_update.emit(self.stats.copy())
                
                # Log batch completion
                self.log.emit(f"✅ Batch {batch_num}/{total_batches}: {batch_processed}/{len(batch)} images indexed")
                
            except Exception as e:
                self.stats['errors'] += len(batch)
                self.log.emit(f"❌ Error in batch {batch_num}: {str(e)}")
                continue
    
    def _update_speed(self):
        """Calculate and emit processing speed."""
        current_time = time.time()
        
        if current_time - self.last_speed_update >= 0.5:  # Update every 0.5s
            elapsed = current_time - self.last_speed_update
            count_diff = self.stats['processed'] - self.last_speed_count
            
            if elapsed > 0:
                speed = count_diff / elapsed
                self.speed.emit(speed)
            
            self.last_speed_update = current_time
            self.last_speed_count = self.stats['processed']


class StatCard(QFrame):
    """Statistics card with icon and value."""
    
    def __init__(self, icon: str, label: str, value: str = "0", parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 36px;")
        
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI", 28, QFont.Bold)
        self.value_label.setFont(font)
        self.value_label.setStyleSheet(f"color: {COLORS['primary']};")
        
        label_text = QLabel(label)
        label_text.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI", 12)
        label_text.setFont(font)
        label_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        layout.addWidget(icon_label)
        layout.addWidget(self.value_label)
        layout.addWidget(label_text)
    
    def set_value(self, value: str):
        """Update value."""
        self.value_label.setText(value)


class IndexScreen(QWidget):
    """Full-page indexing interface."""
    
    completed = Signal(dict)
    
    def __init__(self, batch_indexer, parent=None):
        super().__init__(parent)
        
        self.batch_indexer = batch_indexer
        self.worker = None
        self.start_time = None
        self.folder = None
        
        self.setStyleSheet(f"background: {COLORS['background']};")
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI."""
        # Make the entire screen scrollable
        from PySide6.QtWidgets import QScrollArea
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {COLORS['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {COLORS['background_elevated']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_tertiary']};
            }}
        """)
        
        # Container for scrollable content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(0)  # Remove default spacing
        
        scroll.setWidget(container)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Header (compact)
        header = QLabel("Image Indexing")
        font = QFont("Inter, Segoe UI", 28, QFont.Bold)
        header.setFont(font)
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(header)
        
        # Subtitle (minimal spacing)
        subtitle = QLabel("Extract AI features and index metadata from your local library")
        font = QFont("Inter, Segoe UI", 14)
        subtitle.setFont(font)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-top: 4px;")
        layout.addWidget(subtitle)
        
        # Small gap before folder card
        layout.addSpacing(20)
        
        # Folder selection
        folder_frame = QFrame()
        folder_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        folder_layout = QHBoxLayout(folder_frame)
        
        folder_icon = QLabel("📁")
        folder_icon.setStyleSheet("font-size: 28px;")
        
        folder_info = QVBoxLayout()
        folder_info.setSpacing(4)
        
        folder_title = QLabel("SOURCE FOLDER")
        font = QFont("Inter, Segoe UI", 10, QFont.Bold)
        folder_title.setFont(font)
        folder_title.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        
        self.folder_label = QLabel("No folder selected")
        font = QFont("Inter, Segoe UI", 13)
        self.folder_label.setFont(font)
        self.folder_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        folder_info.addWidget(folder_title)
        folder_info.addWidget(self.folder_label)
        
        self.browse_btn = QPushButton("Browse Folder")
        self.browse_btn.clicked.connect(self._browse_folder)
        font = QFont("Inter, Segoe UI", 12, QFont.Medium)
        self.browse_btn.setFont(font)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedHeight(44)
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        
        folder_layout.addWidget(folder_icon)
        folder_layout.addLayout(folder_info, stretch=1)
        folder_layout.addWidget(self.browse_btn)
        
        layout.addWidget(folder_frame)
        
        layout.addSpacing(20)
        
        # Progress section (initially hidden)
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setSpacing(20)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress header
        progress_header = QLabel("📊 INDEXING PROGRESS")
        font = QFont("Inter, Segoe UI", 12, QFont.Bold)
        progress_header.setFont(font)
        progress_header.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(16)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['background_elevated']};
                border: none;
                border-radius: 8px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_start']}, 
                    stop:1 {COLORS['gradient_end']}
                );
                border-radius: 8px;
            }}
        """)
        
        # Status and speed
        status_row = QHBoxLayout()
        status_row.setSpacing(20)
        
        self.status_label = QLabel("Ready to index")
        font = QFont("Inter, Segoe UI", 13)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        self.speed_label = QLabel("")
        font = QFont("Inter, Segoe UI", 13, QFont.Bold)
        self.speed_label.setFont(font)
        self.speed_label.setStyleSheet(f"color: {COLORS['success']};")
        
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_row.addWidget(self.speed_label)
        
        progress_layout.addWidget(progress_header)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(status_row)
        
        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)
        
        layout.addSpacing(20)
        
        # Statistics cards
        self.stats_container = QWidget()
        stats_layout = QVBoxLayout(self.stats_container)
        stats_layout.setSpacing(16)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        stats_header = QLabel("📈 LIVE STATISTICS")
        font = QFont("Inter, Segoe UI", 12, QFont.Bold)
        stats_header.setFont(font)
        stats_header.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        self.found_card = StatCard("📊", "Images Found", "0")
        self.processed_card = StatCard("✅", "Successfully Indexed", "0")
        self.skipped_card = StatCard("⏭️", "Already Indexed", "0")
        
        cards_layout.addWidget(self.found_card)
        cards_layout.addWidget(self.processed_card)
        cards_layout.addWidget(self.skipped_card)
        
        stats_layout.addWidget(stats_header)
        stats_layout.addLayout(cards_layout)
        
        self.stats_container.setVisible(False)
        layout.addWidget(self.stats_container)
        
        layout.addSpacing(20)
        
        # Time and log
        self.info_container = QWidget()
        info_layout = QVBoxLayout(self.info_container)
        info_layout.setSpacing(16)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        self.time_label = QLabel("⏱️  Time Elapsed: 00:00:00")
        font = QFont("Inter, Segoe UI", 12)
        self.time_label.setFont(font)
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # Log area
        log_header = QLabel("📋 Activity Log")
        font = QFont("Inter, Segoe UI", 11, QFont.Bold)
        log_header.setFont(font)
        log_header.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(200)
        font = QFont("Consolas, Monaco, monospace", 10)
        self.log_area.setFont(font)
        self.log_area.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                color: {COLORS['text_secondary']};
            }}
        """)
        
        info_layout.addWidget(self.time_label)
        info_layout.addWidget(log_header)
        info_layout.addWidget(self.log_area)
        
        self.info_container.setVisible(False)
        layout.addWidget(self.info_container)
        
        layout.addSpacing(40)
        
        # Start button
        self.start_btn = QPushButton("🚀 Start Indexing")
        self.start_btn.clicked.connect(self._start_indexing)
        font = QFont("Inter, Segoe UI", 15, QFont.Bold)
        self.start_btn.setFont(font)
        self.start_btn.setMinimumHeight(56)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background: {COLORS['background_hover']};
                color: {COLORS['text_tertiary']};
            }}
        """)
        self.start_btn.setEnabled(False)
        
        layout.addWidget(self.start_btn)
    
    def _browse_folder(self):
        """Browse for folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Image Folder",
            "data/images"
        )
        
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)
            self.start_btn.setEnabled(True)
            self.log_area.clear()
            self._add_log(f"📁 Selected folder: {folder}")
    
    def _start_indexing(self):
        """Start indexing process."""
        if not self.folder:
            return
        
        # Show progress UI
        self.progress_container.setVisible(True)
        self.stats_container.setVisible(True)
        self.info_container.setVisible(True)
        
        # Reset stats
        self.found_card.set_value("0")
        self.processed_card.set_value("0")
        self.skipped_card.set_value("0")
        self.progress_bar.setValue(0)
        self.speed_label.setText("")
        
        # Disable controls
        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳ Indexing...")
        self.browse_btn.setEnabled(False)
        
        # Start timer
        self.start_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(100)  # Update every 100ms for smooth display
        
        # Create worker
        options = {
            'recursive': True,
            'validate': True,
            'skip_existing': True
        }
        
        self.worker = IndexWorker(self.batch_indexer, self.folder, options)
        self.worker.status.connect(self._update_status)
        self.worker.log.connect(self._add_log)
        self.worker.progress.connect(self._update_progress)
        self.worker.speed.connect(self._update_speed)
        self.worker.stats_update.connect(self._update_stats)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        
        self._add_log("🚀 Starting indexing process...")
        self.worker.start()
    
    def _update_progress(self, current: int, total: int):
        """Update progress bar."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"Processing: {current:,}/{total:,} images ({percentage}%)")
    
    def _update_speed(self, speed: float):
        """Update speed indicator."""
        if speed > 0:
            self.speed_label.setText(f"⚡ {speed:.1f} img/s")
    
    def _update_stats(self, stats: dict):
        """Update statistics cards."""
        self.found_card.set_value(f"{stats.get('found', 0):,}")
        self.processed_card.set_value(f"{stats.get('processed', 0):,}")
        self.skipped_card.set_value(f"{stats.get('skipped', 0):,}")
    
    def _update_status(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
    
    def _add_log(self, message: str):
        """Add log message."""
        self.log_area.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _update_time(self):
        """Update elapsed time."""
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            self.time_label.setText(f"⏱️  Time Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def _on_finished(self, stats: dict):
        """Handle completion."""
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # Update UI
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Indexing complete!")
        self.speed_label.setText("")
        
        # Update final stats
        self.found_card.set_value(f"{stats['found']:,}")
        self.processed_card.set_value(f"{stats['processed']:,}")
        self.skipped_card.set_value(f"{stats['skipped']:,}")
        
        # Re-enable controls
        self.start_btn.setText("✅ Indexing Complete")
        self.browse_btn.setEnabled(True)
        
        self._add_log(f"✅ Successfully indexed {stats['processed']:,} images!")
        self._add_log(f"⏭️ Skipped {stats['skipped']:,} already indexed images")
        
        if stats.get('errors', 0) > 0:
            self._add_log(f"⚠️ {stats['errors']} errors occurred")
        
        # Get total count from metadata store
        try:
            total_in_db = len(self.batch_indexer.metadata_store)
            self._add_log(f"📊 Total in database: {total_in_db:,} images")
        except:
            pass
        
        # Emit signal
        self.completed.emit(stats)
    
    def _on_error(self, error: str):
        """Handle error."""
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        self.status_label.setText(f"❌ Error occurred")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🔄 Retry")
        self.browse_btn.setEnabled(True)
        
        self._add_log(f"❌ Error: {error}")
    
    def reset_to_folder_selection(self):
        """Reset screen to initial state."""
        self.progress_container.setVisible(False)
        self.stats_container.setVisible(False)
        self.info_container.setVisible(False)
        
        self.start_btn.setText("🚀 Start Indexing")
        self.start_btn.setEnabled(bool(self.folder))
        self.browse_btn.setEnabled(True)
        
        self.log_area.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to index")
        self.speed_label.setText("")