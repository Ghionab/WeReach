"""
Global styles and color palette for the application
Professional Dark Theme with Blue Accents
"""

# Professional Dark Theme with Blue Accents
COLORS = {
    # Backgrounds
    'primary_bg': '#1E1E1E',      # Main window background (VS Code dark gray)
    'content_bg': '#252526',      # Content/Panel background (slightly lighter)
    'tertiary_bg': '#2D2D30',     # Input fields, cards
    'hover_bg': '#3E3E42',        # Hover states
    'selection_bg': '#264F78',    # Selection background
    
    # Accents (Blue)
    'primary_accent': '#0078D4',  # Professional Blue (Microsoft/VS Code blue)
    'accent_hover': '#006CA6',    # Darker blue for hover
    'accent_pressed': '#005A8C',  # Even darker for pressed
    'accent_light': '#50E6FF',    # Light blue for highlights/text
    
    # Functional Colors
    'danger': '#F14C4C',          # Error/Delete (Soft Red)
    'danger_hover': '#D13438',
    'success': '#4CAF50',         # Success/Go (Soft Green)
    'success_hover': '#388E3C',
    'warning': '#CCA700',         # Warning (Dark Yellow)
    
    # Text
    'text_primary': '#FFFFFF',    # Main text
    'text_secondary': '#CCCCCC',  # Secondary text, labels
    'text_disabled': '#858585',   # Disabled text
    'text_inverse': '#FFFFFF',    # Text on accent background
    
    # Borders
    'border_default': '#3E3E42',  # Subtle border
    'border_focus': '#0078D4',    # Focus border (Blue)
    'border_light': '#505050',    # Lighter border
}

def get_colors():
    """Return the color palette dictionary"""
    return COLORS

def get_main_style():
    """Return the main QSS stylesheet"""
    return MAIN_STYLE

MAIN_STYLE = f"""
/* Global Reset and Base Styles */
QMainWindow, QDialog {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', 'Roboto', 'Arial', sans-serif;
    font-size: 10pt;
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    outline: none;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border_default']};
    background-color: {COLORS['content_bg']};
    border-radius: 4px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_secondary']};
    padding: 8px 20px;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['content_bg']};
    color: {COLORS['primary_accent']};
    border-bottom: 2px solid {COLORS['primary_accent']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['hover_bg']};
    color: {COLORS['text_primary']};
}}

/* Group Box */
QGroupBox {{
    background-color: {COLORS['content_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 6px;
    margin-top: 24px;
    padding-top: 10px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
    color: {COLORS['primary_accent']};
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['tertiary_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    padding: 6px 16px;
    color: {COLORS['text_primary']};
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLORS['hover_bg']};
    border-color: {COLORS['text_secondary']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_accent']};
    border-color: {COLORS['primary_accent']};
    color: {COLORS['text_inverse']};
}}

QPushButton:disabled {{
    background-color: {COLORS['primary_bg']};
    border-color: {COLORS['border_default']};
    color: {COLORS['text_disabled']};
}}

/* Primary Button */
QPushButton[class="primary-button"] {{
    background-color: {COLORS['primary_accent']};
    border: 1px solid {COLORS['primary_accent']};
    color: {COLORS['text_inverse']};
    font-weight: 600;
}}

QPushButton[class="primary-button"]:hover {{
    background-color: {COLORS['accent_hover']};
    border-color: {COLORS['accent_hover']};
}}

QPushButton[class="primary-button"]:pressed {{
    background-color: {COLORS['accent_pressed']};
    border-color: {COLORS['accent_pressed']};
}}

/* Secondary Button */
QPushButton[class="secondary-button"] {{
    background-color: transparent;
    border: 1px solid {COLORS['border_default']};
    color: {COLORS['text_primary']};
}}

QPushButton[class="secondary-button"]:hover {{
    background-color: {COLORS['hover_bg']};
    border-color: {COLORS['text_secondary']};
}}

/* Danger Button */
QPushButton[class="danger-button"] {{
    background-color: transparent;
    border: 1px solid {COLORS['danger']};
    color: {COLORS['danger']};
}}

QPushButton[class="danger-button"]:hover {{
    background-color: {COLORS['danger']};
    color: {COLORS['text_inverse']};
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['tertiary_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    padding: 6px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['selection_bg']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{
    border: 1px solid {COLORS['primary_accent']};
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover {{
    border: 1px solid {COLORS['text_secondary']};
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
}}

QLabel[class="title"] {{
    font-size: 18pt;
    font-weight: 600;
    color: {COLORS['text_primary']};
    margin-bottom: 10px;
}}

QLabel[class="subtitle"] {{
    font-size: 14pt;
    font-weight: 500;
    color: {COLORS['primary_accent']};
    margin-bottom: 5px;
}}

QLabel[class="section-header"] {{
    font-size: 11pt;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    margin-top: 10px;
    margin-bottom: 5px;
}}

QLabel[class="info-label"] {{
    color: {COLORS['text_secondary']};
    font-size: 9pt;
}}

QLabel[class="status-label"] {{
    font-weight: 500;
    padding: 4px 8px;
    border-radius: 4px;
    background-color: {COLORS['tertiary_bg']};
}}

QLabel[class="error"] {{
    color: {COLORS['danger']};
}}

QLabel[class="success"] {{
    color: {COLORS['success']};
}}

QLabel[class="warning"] {{
    color: {COLORS['warning']};
}}

/* Tables */
QTableWidget {{
    background-color: {COLORS['tertiary_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    gridline-color: {COLORS['border_default']};
    selection-background-color: {COLORS['selection_bg']};
    selection-color: {COLORS['text_primary']};
}}

QHeaderView::section {{
    background-color: {COLORS['content_bg']};
    color: {COLORS['text_secondary']};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {COLORS['border_default']};
    border-right: 1px solid {COLORS['border_default']};
    font-weight: 600;
}}

QTableWidget::item {{
    padding: 4px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: {COLORS['primary_bg']};
    width: 10px;
    margin: 0px 0px 0px 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border_light']};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    border: none;
    background: {COLORS['primary_bg']};
    height: 10px;
    margin: 0px 0px 0px 0px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['border_light']};
    min-width: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['text_secondary']};
}}

/* Progress Bar */
QProgressBar {{
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    text-align: center;
    background-color: {COLORS['tertiary_bg']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary_accent']};
    border-radius: 3px;
}}

/* Combo Box */
QComboBox {{
    background-color: {COLORS['tertiary_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    padding: 6px;
    min-width: 6em;
}}

QComboBox:hover {{
    border: 1px solid {COLORS['text_secondary']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: {COLORS['border_default']};
    border-left-style: solid;
}}

/* Checkbox */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_default']};
    border-radius: 3px;
    background: {COLORS['tertiary_bg']};
}}

QCheckBox::indicator:unchecked:hover {{
    border-color: {COLORS['text_secondary']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary_accent']};
    border-color: {COLORS['primary_accent']};
    image: url(check_icon.png); /* Fallback if no icon */
}}

/* Tooltips */
QToolTip {{
    background-color: {COLORS['tertiary_bg']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_default']};
    padding: 4px;
    border-radius: 4px;
}}
"""