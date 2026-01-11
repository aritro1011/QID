"""
QID - Home Screen (Professional & Stylish)
Redesigned to match professional UI standards.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont

from .theme import COLORS, SPACING, RADIUS


class FeatureCard(QFrame):
    """
    Professional animated card.
    """
    
    clicked = Signal()
    
    def __init__(self, icon: str, title: str, description: str, parent=None):
        super().__init__(parent)
        
        self.setObjectName("feature_card")
        self.setCursor(Qt.PointingHandCursor)
        
        # Professional card styling
        self.setStyleSheet(f"""
            #feature_card {{
                background: {COLORS['glass']};
                border: 1px solid {COLORS['glass_border']};
                border-radius: {RADIUS['xl']};
            }}
            #feature_card:hover {{
                background: rgba(21, 27, 45, 0.9);
                border-color: rgba(79, 108, 255, 0.4);
            }}
        """)
        
        # Layout with proper padding
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(20)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 56px;")
        
        # Title - Professional font
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI, sans-serif", 18, QFont.DemiBold)
        title_label.setFont(font)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            margin-top: 8px;
        """)
        
        # Description - Refined
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setMaximumWidth(280)
        font = QFont("Inter, Segoe UI, sans-serif", 13)
        desc_label.setFont(font)
        desc_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            line-height: 22px;
        """)
        
        # Button - More professional
        button = QPushButton("Get Started")
        button.clicked.connect(self.clicked.emit)
        font = QFont("Inter, Segoe UI, sans-serif", 13, QFont.Medium)
        button.setFont(font)
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_start']}, 
                    stop:1 {COLORS['gradient_end']}
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 28px;
                margin-top: 16px;
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
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(button, alignment=Qt.AlignCenter)
        
        # Subtle animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.92)
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Setup subtle hover animation."""
        self.hover_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def enterEvent(self, event):
        """Hover in."""
        self.hover_animation.stop()
        self.hover_animation.setStartValue(self.opacity_effect.opacity())
        self.hover_animation.setEndValue(1.0)
        self.hover_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hover out."""
        self.hover_animation.stop()
        self.hover_animation.setStartValue(self.opacity_effect.opacity())
        self.hover_animation.setEndValue(0.92)
        self.hover_animation.start()
        super().leaveEvent(event)


class HomeScreen(QWidget):
    """
    Professional home screen matching inspiration designs.
    """
    
    index_clicked = Signal()
    search_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"background: {COLORS['background']};")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content container (centered)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(80, 80, 80, 80)
        content_layout.setSpacing(0)
        content_layout.setAlignment(Qt.AlignCenter)
        
        # Hero Section
        hero_layout = QVBoxLayout()
        hero_layout.setAlignment(Qt.AlignCenter)
        hero_layout.setSpacing(12)
        
        # Title - Professional gradient
        title = QLabel("QID")
        title.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI, sans-serif", 56, QFont.Bold)
        title.setFont(font)
        title.setStyleSheet(f"""
            color: white;
            margin-bottom: 8px;
        """)
        
        # Subtitle - Clean
        subtitle = QLabel("Query Images by Description")
        subtitle.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI, sans-serif", 22)
        subtitle.setFont(font)
        subtitle.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-weight: 400;
        """)
        
        # Tagline - Subtle
        tagline = QLabel("POWERED BY LOCAL AI • PRIVACY FOCUSED")
        tagline.setAlignment(Qt.AlignCenter)
        font = QFont("Inter, Segoe UI, sans-serif", 11, QFont.Medium)
        tagline.setFont(font)
        tagline.setStyleSheet(f"""
            color: {COLORS['text_tertiary']};
            letter-spacing: 1.5px;
            margin-top: 16px;
        """)
        
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addWidget(tagline)
        
        content_layout.addLayout(hero_layout)
        content_layout.addSpacing(64)
        
        # Feature Cards - Side by side
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)
        cards_layout.setAlignment(Qt.AlignCenter)
        
        # Index Card
        self.index_card = FeatureCard(
            icon="📁",
            title="Index Local Library",
            description="Connect your local folders to enable AI-powered searching. Scan and index your photos locally."
        )
        self.index_card.clicked.connect(self.index_clicked.emit)
        self.index_card.setFixedSize(340, 400)
        
        # Search Card
        self.search_card = FeatureCard(
            icon="🔍",
            title="Search My Images",
            description='Find specific photos using natural language queries like "Sunset at the beach" or "Cat sleeping".'
        )
        self.search_card.clicked.connect(self.search_clicked.emit)
        self.search_card.setFixedSize(340, 400)
        
        cards_layout.addWidget(self.index_card)
        cards_layout.addWidget(self.search_card)
        
        content_layout.addLayout(cards_layout)
        content_layout.addSpacing(72)
        
        # Features Footer - FIXED: Proper spacing
        features_container = QWidget()
        features_layout = QHBoxLayout(features_container)
        features_layout.setContentsMargins(0, 0, 0, 0)
        features_layout.setSpacing(64)
        features_layout.setAlignment(Qt.AlignCenter)
        
        # Feature badges
        for icon, text in [
            ("🔒", "100% Offline"),
            ("⚡", "Instant Results"),
            ("🧠", "Neural Engine")
        ]:
            badge = QWidget()
            badge_layout = QVBoxLayout(badge)
            badge_layout.setContentsMargins(0, 0, 0, 0)
            badge_layout.setSpacing(8)
            badge_layout.setAlignment(Qt.AlignCenter)
            
            feature_icon = QLabel(icon)
            feature_icon.setAlignment(Qt.AlignCenter)
            feature_icon.setStyleSheet("font-size: 28px;")
            
            feature_text = QLabel(text)
            feature_text.setAlignment(Qt.AlignCenter)
            font = QFont("Inter, Segoe UI, sans-serif", 12, QFont.Medium)
            feature_text.setFont(font)
            feature_text.setStyleSheet(f"""
                color: {COLORS['text_secondary']};
            """)
            
            badge_layout.addWidget(feature_icon)
            badge_layout.addWidget(feature_text)
            
            features_layout.addWidget(badge)
        
        content_layout.addWidget(features_container)
        content_layout.addStretch()
        
        main_layout.addWidget(content)