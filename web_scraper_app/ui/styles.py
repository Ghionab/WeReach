"""
QSS Styling definitions for the Web Scraper Email Automation Tool
Professional green/black color scheme
"""

# Modern Professional Color Palette - Elegant Dark Theme with Gold Accents
COLORS = {
    # Primary Background Colors
    'primary_bg': '#1e1e1e',       # Very dark charcoal/off-black
    'content_bg': '#2a2a2a',       # Slightly lighter dark gray for cards/inputs
    'tertiary_bg': '#242424',      # Alternative background for zebra striping
    'hover_bg': '#3a3a3a',         # Hover state background
    
    # Accent Colors - The Professional Palette
    'primary_gold': '#D4AF37',     # Rich, modern gold for primary actions
    'gold_hover': '#E6C547',       # Lighter gold for hover states
    'gold_pressed': '#B8860B',     # Darker gold for pressed states
    'secondary_blue': '#0078d4',   # Professional clean blue for secondary actions
    'blue_hover': '#106ebe',       # Darker blue for hover
    'danger_red': '#E74C3C',       # Clear but not overly bright red
    'danger_hover': '#C0392B',     # Darker red for hover
    'success_green': '#27AE60',    # Professional green
    'warning_orange': '#F39C12',   # Professional orange
    
    # Text Colors - High Contrast for Dark Mode
    'text_primary': '#F0F0F0',     # White/very light gray for high contrast
    'text_secondary': '#AAAAAA',   # Medium gray for placeholder/secondary text
    'text_disabled': '#666666',    # Darker gray for disabled text
    'text_white': '#FFFFFF',       # Pure white
    'text_on_gold': '#1e1e1e',     # Dark text for gold backgrounds
    'text_title': '#0078d4',       # Professional blue for titles
    
    # Border and UI Element Colors
    'border_default': '#444444',   # Default border color
    'border_focus': '#D4AF37',     # Gold border for focused elements
    'border_hover': '#0078d4',     # Blue border for hover states
    'scrollbar_bg': '#2a2a2a',     # Scrollbar background
    'scrollbar_handle': '#555555', # Scrollbar handle
    'scrollbar_hover': '#D4AF37',  # Gold scrollbar on hover
}

# Modern Professional Application Style - Elegant Dark Theme with Gold Accents
MAIN_STYLE = f"""
/* ===== MAIN WINDOW & BASE STYLING ===== */
QMainWindow {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', 'Roboto', 'Open Sans', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12pt;
    font-weight: 400;
}}

QWidget {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_primary']};
}}

/* ===== MENU BAR ===== */
QMenuBar {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_primary']};
    border: none;
    border-bottom: 1px solid {COLORS['border_default']};
    padding: 4px 8px;
    font-weight: 500;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 8px 16px;
    margin: 0px 2px;
    border-radius: 4px;
    color: {COLORS['text_primary']};
}}

QMenuBar::item:selected {{
    background-color: {COLORS['content_bg']};
    color: {COLORS['text_primary']};
}}

QMenuBar::item:pressed {{
    background-color: {COLORS['hover_bg']};
    color: {COLORS['text_primary']};
}}

QMenu {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 6px;
    padding: 6px 0px;
}}

QMenu::item {{
    padding: 8px 20px;
    margin: 2px 6px;
    border-radius: 4px;
    color: {COLORS['text_primary']};
}}

QMenu::item:selected {{
    background-color: {COLORS['content_bg']};
    color: {COLORS['text_primary']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border_default']};
    margin: 6px 12px;
}}

/* ===== TAB WIDGET - MAIN NAVIGATION ===== */
QTabWidget::pane {{
    border: 0px;
    background-color: {COLORS['primary_bg']};
    border-radius: 0px;
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 10px 15px;
    margin-right: 2px;
    border-bottom: 2px solid transparent;
    font-weight: 500;
    font-size: 12pt;
    min-width: 100px;
}}

QTabBar::tab:selected {{
    color: {COLORS['primary_gold']};
    border-bottom: 2px solid {COLORS['primary_gold']};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['content_bg']};
    color: {COLORS['text_primary']};
    border-radius: 4px 4px 0px 0px;
}}

/* ===== BUTTONS ===== */
QPushButton {{
    border: none;
    border-radius: 5px;
    padding: 10px 15px;
    font-weight: bold;
    font-size: 12pt;
    min-width: 100px;
    min-height: 16px;
}}

/* Primary Buttons - Gold */
QPushButton[class="primary-button"], 
QPushButton:default {{
    background-color: {COLORS['primary_gold']};
    color: {COLORS['text_on_gold']};
    font-weight: bold;
}}

QPushButton[class="primary-button"]:hover,
QPushButton:default:hover {{
    background-color: {COLORS['gold_hover']};
    color: {COLORS['text_on_gold']};
}}

QPushButton[class="primary-button"]:pressed,
QPushButton:default:pressed {{
    background-color: {COLORS['gold_pressed']};
    color: {COLORS['text_on_gold']};
}}

/* Secondary Buttons - Gold Border */
QPushButton[class="secondary-button"] {{
    background-color: transparent;
    border: 2px solid {COLORS['primary_gold']};
    color: {COLORS['primary_gold']};
    font-weight: bold;
}}

QPushButton[class="secondary-button"]:hover {{
    background-color: {COLORS['primary_gold']};
    color: {COLORS['text_on_gold']};
}}

QPushButton[class="secondary-button"]:pressed {{
    background-color: {COLORS['gold_pressed']};
    color: {COLORS['text_on_gold']};
}}

/* Danger Buttons - Red */
QPushButton[class="danger-button"] {{
    background-color: {COLORS['danger_red']};
    color: {COLORS['text_white']};
    font-weight: bold;
}}

QPushButton[class="danger-button"]:hover {{
    background-color: {COLORS['danger_hover']};
    color: {COLORS['text_white']};
}}

/* Success Buttons - Green */
QPushButton[class="success-button"] {{
    background-color: {COLORS['success_green']};
    color: {COLORS['text_white']};
    font-weight: bold;
}}

QPushButton[class="success-button"]:hover {{
    background-color: #229954;
    color: {COLORS['text_white']};
}}

/* Blue Secondary Actions */
QPushButton[class="blue-button"] {{
    background-color: {COLORS['secondary_blue']};
    color: {COLORS['text_white']};
    font-weight: bold;
}}

QPushButton[class="blue-button"]:hover {{
    background-color: {COLORS['blue_hover']};
    color: {COLORS['text_white']};
}}

/* Disabled Buttons */
QPushButton:disabled {{
    background-color: {COLORS['content_bg']};
    color: {COLORS['text_disabled']};
    border: 1px solid {COLORS['text_disabled']};
}}

/* ===== LABELS ===== */
QLabel {{
    color: {COLORS['text_primary']};
    font-size: 12pt;
    font-weight: 400;
    background-color: transparent;
}}

/* Title Labels - Blue */
QLabel[class="title"] {{
    font-size: 18pt;
    font-weight: bold;
    color: {COLORS['text_title']};
    margin: 8px 0px;
}}

/* Section Headers */
QLabel[class="section-header"] {{
    font-size: 12pt;
    font-weight: bold;
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border_default']};
    margin-top: 10px;
    padding-bottom: 4px;
}}

/* Secondary Text */
QLabel[class="secondary"] {{
    color: {COLORS['text_secondary']};
    font-size: 11pt;
}}

/* Status Labels */
QLabel[class="status-success"] {{
    color: {COLORS['success_green']};
    font-weight: 600;
    background-color: rgba(39, 174, 96, 0.1);
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid {COLORS['success_green']};
}}

QLabel[class="status-error"] {{
    color: {COLORS['danger_red']};
    font-weight: 600;
    background-color: rgba(231, 76, 60, 0.1);
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid {COLORS['danger_red']};
}}

QLabel[class="status-warning"] {{
    color: {COLORS['warning_orange']};
    font-weight: 600;
    background-color: rgba(243, 156, 18, 0.1);
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid {COLORS['warning_orange']};
}}

/* ===== INPUT FIELDS ===== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['content_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    padding: 8px;
    font-size: 12pt;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary_gold']};
    selection-color: {COLORS['text_on_gold']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {COLORS['border_focus']};
    outline: none;
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {COLORS['tertiary_bg']};
    color: {COLORS['text_disabled']};
    border-color: {COLORS['text_disabled']};
}}

QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {{
    color: {COLORS['text_secondary']};
}}

/* ===== TABLES ===== */
QTableWidget {{
    background-color: {COLORS['primary_bg']};
    alternate-background-color: {COLORS['tertiary_bg']};
    border: 1px solid {COLORS['content_bg']};
    gridline-color: {COLORS['content_bg']};
    font-size: 12pt;
    selection-background-color: {COLORS['primary_gold']};
    selection-color: {COLORS['text_on_gold']};
}}

QTableWidget::item {{
    padding: 8px;
    border: none;
    color: {COLORS['text_primary']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary_gold']};
    color: {COLORS['text_on_gold']};
}}

QTableWidget::item:hover {{
    background-color: {COLORS['hover_bg']};
}}

QHeaderView::section {{
    background-color: {COLORS['content_bg']};
    color: {COLORS['primary_gold']};
    padding: 8px;
    font-weight: bold;
    border: none;
    border-right: 1px solid {COLORS['border_default']};
}}

QHeaderView::section:hover {{
    background-color: {COLORS['hover_bg']};
}}

/* ===== PROGRESS BAR ===== */
QProgressBar {{
    background-color: {COLORS['content_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    text-align: center;
    font-weight: 600;
    font-size: 11pt;
    color: {COLORS['text_primary']};
    min-height: 20px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_gold']}, stop:1 {COLORS['gold_hover']});
    border-radius: 3px;
}}

/* ===== COMBO BOX ===== */
QComboBox {{
    background-color: {COLORS['content_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    padding: 8px 12px;
    min-width: 120px;
    font-size: 12pt;
    color: {COLORS['text_primary']};
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox:hover {{
    border-color: {COLORS['border_hover']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['content_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    selection-background-color: {COLORS['primary_gold']};
    selection-color: {COLORS['text_on_gold']};
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    border-radius: 2px;
    margin: 1px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {COLORS['hover_bg']};
    color: {COLORS['text_primary']};
}}

/* ===== SCROLL BARS ===== */
QScrollArea {{
    border: none;
    background-color: {COLORS['primary_bg']};
}}

QScrollBar:vertical {{
    background-color: {COLORS['scrollbar_bg']};
    width: 12px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['scrollbar_handle']};
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['scrollbar_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['scrollbar_bg']};
    height: 12px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['scrollbar_handle']};
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['scrollbar_hover']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ===== GROUP BOX ===== */
QGroupBox {{
    font-weight: 600;
    font-size: 13pt;
    border: 1px solid {COLORS['border_default']};
    border-radius: 6px;
    margin-top: 15px;
    padding-top: 15px;
    padding-left: 8px;
    padding-right: 8px;
    padding-bottom: 10px;
    background-color: {COLORS['primary_bg']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 15px;
    padding: 2px 8px;
    color: {COLORS['text_title']};
    background-color: {COLORS['primary_bg']};
    font-size: 13pt;
    font-weight: bold;
}}

/* ===== CHECKBOXES ===== */
QCheckBox {{
    color: {COLORS['text_primary']};
    font-size: 12pt;
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLORS['border_default']};
    border-radius: 3px;
    background-color: {COLORS['content_bg']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['border_focus']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary_gold']};
    border-color: {COLORS['primary_gold']};
}}

/* ===== SPIN BOX ===== */
QSpinBox {{
    background-color: {COLORS['content_bg']};
    border: 1px solid {COLORS['border_default']};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12pt;
    color: {COLORS['text_primary']};
    min-width: 80px;
}}

QSpinBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    width: 18px;
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
    background-color: {COLORS['content_bg']};
    color: {COLORS['text_white']};
    border: 1px solid {COLORS['primary_gold']};
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 11pt;
    font-weight: 500;
}}

/* ===== DIALOG BOXES ===== */
QDialog {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_primary']};
}}

QMessageBox {{
    background-color: {COLORS['primary_bg']};
    color: {COLORS['text_primary']};
}}

QMessageBox QPushButton {{
    min-width: 80px;
    padding: 8px 16px;
}}

/* ===== SPLITTER ===== */
QSplitter::handle {{
    background-color: {COLORS['border_default']};
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
    background-color: {COLORS['primary_gold']};
}}
"""

def get_main_style():
    """Return the main application stylesheet"""
    return MAIN_STYLE

def get_colors():
    """Return the color palette dictionary"""
    return COLORS