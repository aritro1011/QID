"""
QID - Settings Screen
Application settings and database management.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from .theme import COLORS


class SettingCard(QFrame):
    """Individual setting card."""
    
    def __init__(self, icon: str, title: str, description: str, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 24px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px;")
        
        title_label = QLabel(title)
        font = QFont("Inter, Segoe UI", 16, QFont.Bold)
        title_label.setFont(font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Description
        desc_label = QLabel(description)
        font = QFont("Inter, Segoe UI", 12)
        desc_label.setFont(font)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc_label.setWordWrap(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(desc_label)


class ActionCard(QFrame):
    """Card with action buttons."""
    
    button_clicked = Signal(str)
    
    def __init__(self, title: str, description: str, buttons: list, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 24px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel(title)
        font = QFont("Inter, Segoe UI", 14, QFont.Bold)
        title_label.setFont(font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        # Description
        desc_label = QLabel(description)
        font = QFont("Inter, Segoe UI", 11)
        desc_label.setFont(font)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
        # Buttons
        for btn_config in buttons:
            btn = self._create_button(
                btn_config['text'],
                btn_config['style'],
                btn_config['action']
            )
            layout.addWidget(btn)
    
    def _create_button(self, text: str, style: str, action: str):
        """Create styled button."""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(44)
        font = QFont("Inter, Segoe UI", 12, QFont.Medium)
        btn.setFont(font)
        btn.clicked.connect(lambda: self.button_clicked.emit(action))
        
        if style == "primary":
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background: {COLORS['primary_hover']};
                }}
            """)
        elif style == "danger":
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['error']};
                    border: 1px solid {COLORS['error']};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background: {COLORS['error']};
                    color: white;
                }}
            """)
        else:  # secondary
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background: {COLORS['background_hover']};
                    color: {COLORS['text_primary']};
                }}
            """)
        
        return btn


class SettingsScreen(QWidget):
    """Settings and configuration page."""
    
    # Signals
    model_changed = Signal(str)
    hardware_changed = Signal(str)
    rebuild_index = Signal()
    clear_cache = Signal()
    delete_index = Signal()
    
    def __init__(self, batch_indexer, parent=None):
        super().__init__(parent)
        
        self.batch_indexer = batch_indexer
        
        self.setStyleSheet(f"background: {COLORS['background']};")
        
        self._create_ui()
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+, to open settings (standard shortcut)
        settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        settings_shortcut.activated.connect(lambda: self.setFocus())
        
        # Ctrl+Shift+S alternative
        alt_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        alt_shortcut.activated.connect(lambda: self.setFocus())
    
    def _create_ui(self):
        """Create settings UI with scrollability."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
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
        layout.setSpacing(32)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Header
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        header = QLabel("Application Settings")
        font = QFont("Inter, Segoe UI", 28, QFont.Bold)
        header.setFont(font)
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        subtitle = QLabel("Configure AI models, hardware acceleration, and library management")
        font = QFont("Inter, Segoe UI", 14)
        subtitle.setFont(font)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        header_layout.addWidget(header)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_container)
        layout.addSpacing(12)
        
        # Model Configuration Section
        model_header = QLabel("🤖 Model Configuration")
        font = QFont("Inter, Segoe UI", 18, QFont.Bold)
        model_header.setFont(font)
        model_header.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        layout.addWidget(model_header)
        
        model_card = SettingCard(
            "🎯",
            "Active AI Model",
            "Select the vision model used for image embedding and vector generation."
        )
        
        # Model selector
        model_selector_layout = QHBoxLayout()
        
        model_label = QLabel("Model:")
        font = QFont("Inter, Segoe UI", 12)
        model_label.setFont(font)
        model_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "ViT-B/32 (Fast, Recommended)",
            "ViT-B/16 (Better Quality)",
            "ViT-L/14 (Best Quality, Slower)"
        ])
        self.model_combo.setCurrentIndex(0)
        font = QFont("Inter, Segoe UI", 12)
        self.model_combo.setFont(font)
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 16px;
                color: {COLORS['text_primary']};
                min-width: 300px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        
        model_selector_layout.addWidget(model_label)
        model_selector_layout.addWidget(self.model_combo)
        model_selector_layout.addStretch()
        
        model_card.layout().addLayout(model_selector_layout)
        
        # Warning
        warning = QLabel("ℹ️  Changing the model requires a full library re-index. Previously generated vectors will be incompatible with the new architecture.")
        font = QFont("Inter, Segoe UI", 11)
        warning.setFont(font)
        warning.setStyleSheet(f"""
            background: rgba(79, 108, 255, 0.1);
            border: 1px solid rgba(79, 108, 255, 0.3);
            border-radius: 8px;
            padding: 12px;
            color: {COLORS['primary']};
        """)
        warning.setWordWrap(True)
        
        model_card.layout().addWidget(warning)
        
        layout.addWidget(model_card)
        
        # Hardware Acceleration Section
        hw_header = QLabel("⚡ Hardware Acceleration")
        font = QFont("Inter, Segoe UI", 18, QFont.Bold)
        hw_header.setFont(font)
        hw_header.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        layout.addWidget(hw_header)
        
        hw_card = SettingCard(
            "🎮",
            "Processing Unit",
            "Choose between your graphics card (GPU) or main processor (CPU) for inference."
        )
        
        # Hardware selector
        hw_selector_layout = QHBoxLayout()
        
        self.gpu_btn = QPushButton("🎮 GPU (CUDA)")
        self.gpu_btn.setCheckable(True)
        self.gpu_btn.setChecked(True)
        self.gpu_btn.clicked.connect(self._on_gpu_selected)
        
        self.cpu_btn = QPushButton("💻 CPU Only")
        self.cpu_btn.setCheckable(True)
        self.cpu_btn.clicked.connect(self._on_cpu_selected)
        
        for btn in [self.gpu_btn, self.cpu_btn]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(44)
            btn.setMinimumWidth(150)
            font = QFont("Inter, Segoe UI", 12, QFont.Medium)
            btn.setFont(font)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    padding: 0 24px;
                }}
                QPushButton:hover {{
                    background: {COLORS['background_hover']};
                    color: {COLORS['text_primary']};
                }}
                QPushButton:checked {{
                    background: {COLORS['primary']};
                    color: white;
                    border-color: {COLORS['primary']};
                }}
            """)
        
        hw_selector_layout.addWidget(self.gpu_btn)
        hw_selector_layout.addWidget(self.cpu_btn)
        hw_selector_layout.addStretch()
        
        hw_card.layout().addLayout(hw_selector_layout)
        
        layout.addWidget(hw_card)
        
        # Index Management Section
        idx_header = QLabel("💾 Index Management")
        font = QFont("Inter, Segoe UI", 18, QFont.Bold)
        idx_header.setFont(font)
        idx_header.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        layout.addWidget(idx_header)
        
        # Three cards in a row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Maintenance card
        maintenance_card = ActionCard(
            "Maintenance",
            "Sync the database with current local files.",
            [{
                'text': '🔄 Rebuild Index',
                'style': 'primary',
                'action': 'rebuild'
            }]
        )
        maintenance_card.button_clicked.connect(self._on_action)
        
        # Optimization card
        optimization_card = ActionCard(
            "Optimization",
            "Remove temporary metadata and thumbnails.",
            [{
                'text': '🗑️ Clear Cache',
                'style': 'secondary',
                'action': 'clear_cache'
            }]
        )
        optimization_card.button_clicked.connect(self._on_action)
        
        # Danger Zone card
        danger_card = ActionCard(
            "Danger Zone",
            "Irreversibly delete all vector data for this library.",
            [{
                'text': '🗑️ Delete Index',
                'style': 'danger',
                'action': 'delete'
            }]
        )
        danger_card.button_clicked.connect(self._on_action)
        
        cards_layout.addWidget(maintenance_card)
        cards_layout.addWidget(optimization_card)
        cards_layout.addWidget(danger_card)
        
        layout.addLayout(cards_layout)
        
        layout.addSpacing(20)
        
        # System Info Footer
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['background_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        info_layout = QHBoxLayout(info_frame)
        
        system_status = QLabel("🟢 SYSTEM READY")
        font = QFont("Inter, Segoe UI", 10, QFont.Bold)
        system_status.setFont(font)
        system_status.setStyleSheet(f"color: {COLORS['success']};")
        
        library_size = QLabel(f"Library: {len(self.batch_indexer.metadata_store):,} images")
        font = QFont("Inter, Segoe UI", 11)
        library_size.setFont(font)
        library_size.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        info_layout.addWidget(system_status)
        info_layout.addStretch()
        info_layout.addWidget(library_size)
        
        layout.addWidget(info_frame)
        
        layout.addSpacing(40)
    
    def _on_gpu_selected(self):
        """Handle GPU selection."""
        self.cpu_btn.setChecked(False)
        self.hardware_changed.emit("cuda")
    
    def _on_cpu_selected(self):
        """Handle CPU selection."""
        self.gpu_btn.setChecked(False)
        self.hardware_changed.emit("cpu")
    
    def _on_action(self, action: str):
        """Handle action button clicks."""
        if action == "rebuild":
            reply = QMessageBox.question(
                self,
                "Rebuild Index",
                "This will re-index all images in your library. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.rebuild_index.emit()
        
        elif action == "clear_cache":
            reply = QMessageBox.question(
                self,
                "Clear Cache",
                "This will clear temporary files and thumbnails. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.clear_cache.emit()
        
        elif action == "delete":
            reply = QMessageBox.warning(
                self,
                "Delete Index",
                "⚠️ WARNING: This will permanently delete all indexed data!\n\n"
                "Are you absolutely sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Double confirmation
                reply2 = QMessageBox.critical(
                    self,
                    "Final Confirmation",
                    "This action CANNOT be undone!\n\n"
                    "Really delete everything?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply2 == QMessageBox.Yes:
                    self.delete_index.emit()