"""
QID - Modern Dark Theme
Color palette and styling system inspired by modern design trends.
"""

# Color Palette (from your UI designs)
COLORS = {
    # Backgrounds
    'background': '#0a0e1a',          # Deep navy background
    'background_elevated': '#151b2d',  # Card/elevated surfaces
    'background_hover': '#1e293b',     # Hover state
    
    # Primary colors (Blue-Purple gradient)
    'primary': '#4f6cff',              # Primary blue
    'primary_hover': '#6b82ff',        # Lighter blue
    'primary_pressed': '#3d54d9',      # Darker blue
    
    # Accent gradient
    'gradient_start': '#667eea',       # Blue
    'gradient_end': '#764ba2',         # Purple
    
    # Success/Status
    'success': '#00ff94',              # Green
    'warning': '#ffa726',              # Orange
    'error': '#ff5252',                # Red
    'info': '#4f6cff',                 # Blue
    
    # Text
    'text_primary': '#ffffff',         # White
    'text_secondary': '#8b92a8',       # Gray
    'text_tertiary': '#4a5568',        # Darker gray
    
    # Borders & Overlays
    'border': '#1e293b',               # Subtle borders
    'border_focus': '#4f6cff',         # Focused elements
    'overlay': 'rgba(10, 14, 26, 0.9)', # Modal overlay
    
    # Glassmorphism
    'glass': 'rgba(21, 27, 45, 0.7)',  # Translucent cards
    'glass_border': 'rgba(255, 255, 255, 0.1)',
}

# Typography
FONTS = {
    'family': 'Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif',
    'mono': 'Consolas, Monaco, monospace',
    
    'size_xs': '11px',
    'size_sm': '13px',
    'size_base': '14px',
    'size_lg': '16px',
    'size_xl': '20px',
    'size_2xl': '24px',
    'size_3xl': '32px',
    'size_4xl': '48px',
}

# Spacing (consistent spacing scale)
SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '24px',
    'xl': '32px',
    '2xl': '48px',
}

# Border Radius
RADIUS = {
    'sm': '4px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    '2xl': '24px',
    'full': '9999px',
}

# Shadows (subtle, modern)
SHADOWS = {
    'sm': '0 2px 4px rgba(0, 0, 0, 0.3)',
    'md': '0 4px 12px rgba(0, 0, 0, 0.4)',
    'lg': '0 8px 24px rgba(0, 0, 0, 0.5)',
    'xl': '0 16px 48px rgba(0, 0, 0, 0.6)',
    'glow': '0 0 20px rgba(79, 108, 255, 0.3)',
}

# Animation Durations (Apple-style subtle)
DURATION = {
    'fast': 150,      # Quick feedback
    'normal': 250,    # Standard transitions
    'slow': 400,      # Page transitions
}

# Easing Curves
EASING = {
    'ease_out': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
    'ease_in_out': 'cubic-bezier(0.65, 0.05, 0.36, 1)',
    'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
}


def get_stylesheet() -> str:
    """
    Generate the complete QSS stylesheet.
    QSS (Qt Style Sheets) is like CSS for Qt applications.
    """
    return f"""
    /* Global Application Styles */
    QWidget {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
        font-family: {FONTS['family']};
        font-size: {FONTS['size_base']};
    }}
    
    /* Main Window */
    QMainWindow {{
        background-color: {COLORS['background']};
    }}
    
    /* Buttons - Primary (Gradient) */
    QPushButton {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['gradient_start']}, 
            stop:1 {COLORS['gradient_end']}
        );
        color: {COLORS['text_primary']};
        border: none;
        border-radius: {RADIUS['md']};
        padding: 10px 20px;
        font-weight: 600;
        font-size: {FONTS['size_base']};
    }}
    
    QPushButton:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['primary_hover']}, 
            stop:1 #8b5cb8
        );
    }}
    
    QPushButton:pressed {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['primary_pressed']}, 
            stop:1 #6843a0
        );
    }}
    
    QPushButton:disabled {{
        background: {COLORS['background_hover']};
        color: {COLORS['text_tertiary']};
    }}
    
    /* Buttons - Secondary (Ghost) */
    QPushButton[buttonStyle="secondary"] {{
        background: transparent;
        border: 1px solid {COLORS['border']};
        color: {COLORS['text_secondary']};
    }}
    
    QPushButton[buttonStyle="secondary"]:hover {{
        background: {COLORS['background_hover']};
        border-color: {COLORS['border_focus']};
        color: {COLORS['text_primary']};
    }}
    
    /* Input Fields */
    QLineEdit {{
        background: {COLORS['background_elevated']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['md']};
        padding: 12px 16px;
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_base']};
    }}
    
    QLineEdit:focus {{
        border-color: {COLORS['border_focus']};
        background: {COLORS['background_hover']};
    }}
    
    QLineEdit::placeholder {{
        color: {COLORS['text_tertiary']};
    }}
    
    /* Cards/Frames */
    QFrame[frameStyle="card"] {{
        background: {COLORS['glass']};
        border: 1px solid {COLORS['glass_border']};
        border-radius: {RADIUS['xl']};
    }}
    
    QFrame[frameStyle="card"]:hover {{
        background: rgba(21, 27, 45, 0.8);
        border-color: rgba(255, 255, 255, 0.15);
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background: {COLORS['background_elevated']};
        border: none;
        border-radius: {RADIUS['sm']};
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['gradient_start']}, 
            stop:1 {COLORS['gradient_end']}
        );
        border-radius: {RADIUS['sm']};
    }}
    
    /* Scroll Bars */
    QScrollBar:vertical {{
        background: {COLORS['background']};
        width: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS['background_hover']};
        border-radius: 6px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['text_tertiary']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background: {COLORS['background']};
        height: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {COLORS['background_hover']};
        border-radius: 6px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS['text_tertiary']};
    }}
    
    /* Labels */
    QLabel {{
        color: {COLORS['text_primary']};
        background: transparent;
    }}
    
    QLabel[labelStyle="title"] {{
        font-size: {FONTS['size_3xl']};
        font-weight: 700;
    }}
    
    QLabel[labelStyle="subtitle"] {{
        font-size: {FONTS['size_lg']};
        color: {COLORS['text_secondary']};
    }}
    
    QLabel[labelStyle="badge"] {{
        background: {COLORS['success']};
        color: {COLORS['background']};
        border-radius: {RADIUS['full']};
        padding: 4px 12px;
        font-size: {FONTS['size_xs']};
        font-weight: 700;
    }}
    
    /* Menu Bar */
    QMenuBar {{
        background: {COLORS['background_elevated']};
        border-bottom: 1px solid {COLORS['border']};
        padding: 4px;
    }}
    
    QMenuBar::item {{
        background: transparent;
        padding: 8px 16px;
        border-radius: {RADIUS['md']};
    }}
    
    QMenuBar::item:selected {{
        background: {COLORS['background_hover']};
    }}
    
    QMenu {{
        background: {COLORS['background_elevated']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['md']};
        padding: 8px;
    }}
    
    QMenu::item {{
        padding: 8px 24px;
        border-radius: {RADIUS['sm']};
    }}
    
    QMenu::item:selected {{
        background: {COLORS['background_hover']};
    }}
    
    /* Status Bar */
    QStatusBar {{
        background: {COLORS['background_elevated']};
        border-top: 1px solid {COLORS['border']};
        color: {COLORS['text_secondary']};
    }}
    
    /* Tool Tips */
    QToolTip {{
        background: {COLORS['background_elevated']};
        border: 1px solid {COLORS['border']};
        color: {COLORS['text_primary']};
        padding: 8px;
        border-radius: {RADIUS['md']};
    }}
    """


def get_card_style() -> str:
    """Style for card components."""
    return f"""
        background: {COLORS['glass']};
        border: 1px solid {COLORS['glass_border']};
        border-radius: {RADIUS['xl']};
        padding: {SPACING['lg']};
    """


def get_gradient_text_style() -> str:
    """Gradient text effect (for titles) - Qt doesn't support webkit."""
    # Note: QSS doesn't support gradient text like CSS
    # Use solid primary color instead
    return f"""
        color: {COLORS['primary']};
        font-weight: 700;
    """