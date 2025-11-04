"""
QSS Styling definitions for the Web Scraper Email Automation Tool
Professional green/black color scheme
"""

# Professional Dark Mode Color Palette - Modern & Readable
COLORS = {
    # Primary colors - Dark theme with blue accents
    'primary_navy': '#2196F3',      # Bright blue for accents
    'dark_navy': '#1976D2',        # Darker blue for hover
    'medium_navy': '#42A5F5',      # Medium blue for highlights
    'light_navy': '#64B5F6',       # Light blue for subtle accents
    
    # Neutral colors - Dark mode
    'primary_dark': '#121212',     # Very dark background (Material Design)
    'secondary_dark': '#1E1E1E',   # Secondary dark background
    'light_gray': '#2D2D2D',       # Dark gray for cards/panels
    'medium_gray': '#3D3D3D',      # Medium gray for borders
    'dark_gray': '#4D4D4D',        # Lighter gray for subtle elements
    'border_gray': '#404040',      # Dark border color
    'white': '#FFFFFF',            # Pure white for contrast
    
    # Status colors - Dark mode friendly
    'success_green': '#4CAF50',    # Bright green for success
    'error_red': '#F44336',        # Bright red for errors
    'warning_orange': '#FF9800',   # Orange for warnings
    'info_blue': '#2196F3',        # Blue for info
    
    # Text colors - Dark mode optimized
    'text_primary': '#FFFFFF',     # White text for dark backgrounds
    'text_secondary': '#B0B0B0',   # Light gray for secondary text
    'text_disabled': '#757575',    # Medium gray for disabled text
    'text_white': '#FFFFFF',       # Pure white
    'text_on_navy': '#FFFFFF',     # White text on blue backgrounds
    
    # Background colors - Dark mode
    'bg_primary': '#121212',       # Primary dark background
    'bg_secondary': '#1E1E1E',     # Secondary dark background
    'bg_tertiary': '#2D2D2D',      # Tertiary background for cards
    'bg_dark': '#0D0D0D',          # Even darker for contrast
    'bg_input': '#2D2D2D',         # Dark input field background
    'bg_hover': '#3D3D3D'          # Hover state background
}

# Modern Professional Application Style
MAIN_STYLE = f"""
/* ===== MAIN WINDOW ===== */
QMainWindow {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12pt;
    font-weight: 400;
}}

/* ===== MENU BAR ===== */
QMenuBar {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    border: none;
    border-bottom: 1px solid {COLORS['border_gray']};
    padding: 2px 8px;
    font-weight: 500;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 8px 16px;
    margin: 0px 2px;
    border-radius: 6px;
    color: {COLORS['text_primary']};
}}

QMenuBar::item:selected {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
}}

QMenuBar::item:pressed {{
    background-color: {COLORS['dark_navy']};
    color: {COLORS['text_white']};
}}

QMenu {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_gray']};
    border-radius: 8px;
    padding: 8px 0px;
}}

QMenu::item {{
    padding: 10px 20px;
    margin: 2px 8px;
    border-radius: 6px;
    color: {COLORS['text_primary']};
}}

QMenu::item:selected {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border_gray']};
    margin: 8px 16px;
}}

/* ===== STATUS BAR ===== */
QStatusBar {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_white']};
    border: none;
    padding: 6px 12px;
    font-size: 10pt;
}}

QStatusBar QLabel {{
    color: {COLORS['text_white']};
    padding: 0px 8px;
}}

/* ===== TAB WIDGET ===== */
QTabWidget::pane {{
    border: 1px solid {COLORS['border_gray']};
    background-color: {COLORS['bg_primary']};
    border-radius: 8px;
    margin-top: -1px;
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_secondary']};
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 120px;
    font-weight: 500;
    border: 1px solid {COLORS['border_gray']};
    border-bottom: none;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
    border-color: {COLORS['primary_navy']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['medium_navy']};
    color: {COLORS['text_white']};
    border-color: {COLORS['medium_navy']};
}}

/* ===== TAB CONTENT AREAS - Fix white background ===== */
QWidget[class="tab-content"] {{
    background-color: {COLORS['bg_primary']};
}}

/* Ensure all tab content widgets use dark background */
QTabWidget > QWidget {{
    background-color: {COLORS['bg_primary']};
}}

QScrollArea QWidget {{
    background-color: {COLORS['bg_primary']};
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 12pt;
    min-width: 120px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['dark_navy']};
}}

QPushButton:pressed {{
    background-color: {COLORS['dark_navy']};
}}

QPushButton:disabled {{
    background-color: {COLORS['medium_gray']};
    color: {COLORS['text_disabled']};
}}

/* Primary Button */
QPushButton[class="primary-button"] {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
    font-weight: 600;
    padding: 14px 28px;
    font-size: 13pt;
}}

QPushButton[class="primary-button"]:hover {{
    background-color: {COLORS['dark_navy']};
}}

/* Secondary Button */
QPushButton[class="secondary-button"] {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['primary_navy']};
    border: 2px solid {COLORS['primary_navy']};
    font-weight: 600;
    font-size: 12pt;
}}

QPushButton[class="secondary-button"]:hover {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
}}

/* Danger Button */
QPushButton[class="danger-button"] {{
    background-color: {COLORS['error_red']};
    color: {COLORS['text_white']};
    font-weight: 600;
}}

QPushButton[class="danger-button"]:hover {{
    background-color: #D32F2F;
}}

/* Success Button */
QPushButton[class="success-button"] {{
    background-color: {COLORS['success_green']};
    color: {COLORS['text_white']};
    font-weight: 600;
}}

QPushButton[class="success-button"]:hover {{
    background-color: #388E3C;
}}

/* ===== INPUT FIELDS ===== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_input']};
    border: 2px solid {COLORS['border_gray']};
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 12pt;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['medium_navy']};
    selection-color: {COLORS['text_white']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['primary_navy']};
    outline: none;
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_disabled']};
    border-color: {COLORS['medium_gray']};
}}

QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {{
    color: {COLORS['text_secondary']};
}}

/* ===== LABELS ===== */
QLabel {{
    color: {COLORS['text_primary']};
    font-size: 12pt;
    font-weight: 400;
}}

QLabel[class="title"] {{
    font-size: 20pt;
    font-weight: 700;
    color: {COLORS['primary_navy']};
    margin: 16px 0px 12px 0px;
}}

QLabel[class="subtitle"] {{
    font-size: 16pt;
    font-weight: 600;
    color: {COLORS['text_primary']};
    margin: 12px 0px 8px 0px;
}}

QLabel[class="info-label"] {{
    font-size: 12pt;
    color: {COLORS['text_secondary']};
    font-weight: 500;
}}

QLabel[class="status-label"] {{
    font-size: 12pt;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
}}

QLabel[class="error"] {{
    color: {COLORS['error_red']};
    font-weight: 600;
    background-color: rgba(244, 67, 54, 0.1);
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid {COLORS['error_red']};
}}

QLabel[class="success"] {{
    color: {COLORS['success_green']};
    font-weight: 600;
    background-color: rgba(76, 175, 80, 0.1);
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid {COLORS['success_green']};
}}

QLabel[class="warning"] {{
    color: {COLORS['warning_orange']};
    font-weight: 600;
    background-color: rgba(255, 152, 0, 0.1);
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid {COLORS['warning_orange']};
}}

/* ===== TABLES ===== */
QTableWidget {{
    background-color: {COLORS['bg_primary']};
    alternate-background-color: {COLORS['bg_secondary']};
    border: 2px solid {COLORS['border_gray']};
    border-radius: 10px;
    gridline-color: {COLORS['border_gray']};
    font-size: 12pt;
    selection-background-color: {COLORS['medium_navy']};
    min-height: 200px;
}}

QTableWidget::item {{
    padding: 15px 12px;
    border: none;
    color: {COLORS['text_primary']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
}}

QTableWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

QHeaderView::section {{
    background-color: {COLORS['primary_navy']};
    color: {COLORS['text_white']};
    padding: 16px 12px;
    border: none;
    font-weight: 700;
    font-size: 13pt;
}}

QHeaderView::section:hover {{
    background-color: {COLORS['dark_navy']};
}}

QHeaderView::section:first {{
    border-top-left-radius: 8px;
}}

QHeaderView::section:last {{
    border-top-right-radius: 8px;
}}

/* ===== PROGRESS BAR ===== */
QProgressBar {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border_gray']};
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
    font-size: 11pt;
    color: {COLORS['text_primary']};
    min-height: 20px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_navy']}, stop:1 {COLORS['medium_navy']});
    border-radius: 7px;
}}

/* ===== COMBO BOX ===== */
QComboBox {{
    background-color: {COLORS['bg_primary']};
    border: 2px solid {COLORS['border_gray']};
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 120px;
    font-size: 11pt;
    color: {COLORS['text_primary']};
}}

QComboBox:focus {{
    border-color: {COLORS['primary_navy']};
}}

QComboBox:hover {{
    border-color: {COLORS['medium_navy']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_gray']};
    border-radius: 6px;
    selection-background-color: {COLORS['primary_navy']};
    selection-color: {COLORS['text_white']};
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 10px 14px;
    border-radius: 4px;
    margin: 2px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {COLORS['medium_navy']};
    color: {COLORS['text_white']};
}}

/* ===== SCROLL BARS ===== */
QScrollArea {{
    border: none;
    background-color: {COLORS['bg_primary']};
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_tertiary']};
    width: 16px;
    border-radius: 8px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['dark_gray']};
    border-radius: 8px;
    min-height: 40px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['primary_navy']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_tertiary']};
    height: 16px;
    border-radius: 8px;
    margin: 2px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['dark_gray']};
    border-radius: 8px;
    min-width: 40px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['primary_navy']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ===== GROUP BOX ===== */
QGroupBox {{
    font-weight: 600;
    font-size: 13pt;
    border: 2px solid {COLORS['border_gray']};
    border-radius: 10px;
    margin-top: 20px;
    padding-top: 20px;
    padding-left: 10px;
    padding-right: 10px;
    padding-bottom: 15px;
    background-color: {COLORS['bg_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 20px;
    padding: 4px 12px;
    color: {COLORS['primary_navy']};
    background-color: {COLORS['bg_primary']};
    font-size: 14pt;
    font-weight: 700;
    border: 1px solid {COLORS['border_gray']};
    border-radius: 6px;
}}

/* ===== SPLITTER ===== */
QSplitter::handle {{
    background-color: {COLORS['border_gray']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
    margin: 2px 0px;
}}

QSplitter::handle:vertical {{
    height: 2px;
    margin: 0px 2px;
}}

QSplitter::handle:pressed {{
    background-color: {COLORS['primary_navy']};
}}

/* ===== CHECKBOXES ===== */
QCheckBox {{
    color: {COLORS['text_primary']};
    font-size: 11pt;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border_gray']};
    border-radius: 4px;
    background-color: {COLORS['bg_primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary_navy']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary_navy']};
    border-color: {COLORS['primary_navy']};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
}}

/* ===== SPIN BOX ===== */
QSpinBox {{
    background-color: {COLORS['bg_primary']};
    border: 2px solid {COLORS['border_gray']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 11pt;
    color: {COLORS['text_primary']};
    min-width: 80px;
}}

QSpinBox:focus {{
    border-color: {COLORS['primary_navy']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    width: 20px;
    border: none;
    background-color: transparent;
}}

QSpinBox::up-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid {COLORS['text_secondary']};
}}

QSpinBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid {COLORS['text_secondary']};
}}

/* ===== TOOLTIPS ===== */
QToolTip {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_white']};
    border: 1px solid {COLORS['primary_navy']};
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 11pt;
    font-weight: 500;
}}

/* ===== DIALOG BOXES ===== */
QDialog {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

QMessageBox {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

QMessageBox QPushButton {{
    min-width: 80px;
    padding: 8px 16px;
}}
"""

def get_main_style():
    """Return the main application stylesheet"""
    return MAIN_STYLE

def get_colors():
    """Return the color palette dictionary"""
    return COLORS