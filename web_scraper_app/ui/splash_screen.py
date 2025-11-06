"""
Modern, professional splash screen for application startup
Features elegant dark design with gold accents
"""

from PyQt6.QtWidgets import (
    QSplashScreen, QLabel, QProgressBar, QVBoxLayout, 
    QWidget, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPen, QBrush, QLinearGradient
import time


class ModernSplashScreen(QSplashScreen):
    """
    Modern, professional splash screen with elegant dark design and gold accents
    """
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    
    def __init__(self):
        # Create modern splash screen pixmap
        pixmap = QPixmap(500, 350)
        pixmap.fill(QColor(30, 30, 30))  # Primary Background (#1e1e1e)
        
        # Draw modern design on pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 0, 350)
        gradient.setColorAt(0, QColor(30, 30, 30))    # #1e1e1e
        gradient.setColorAt(1, QColor(42, 42, 42))    # #2a2a2a
        painter.fillRect(0, 0, 500, 350, QBrush(gradient))
        
        # Draw subtle border
        painter.setPen(QPen(QColor(68, 68, 68), 2))  # #444444
        painter.drawRect(1, 1, 498, 348)
        
        # Set up fonts - Modern sans-serif
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        subtitle_font = QFont("Segoe UI", 14, QFont.Weight.Normal)
        version_font = QFont("Segoe UI", 10, QFont.Weight.Normal)
        
        # Draw main title in white
        painter.setPen(QPen(QColor(240, 240, 240)))  # #F0F0F0
        painter.setFont(title_font)
        title_rect = QRect(30, 60, 440, 40)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "Web Scraper Email Automation")
        
        # Draw subtitle in secondary text color
        painter.setPen(QPen(QColor(170, 170, 170)))  # #AAAAAA
        painter.setFont(subtitle_font)
        subtitle_rect = QRect(30, 110, 440, 25)
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, "Professional Email Outreach Tool")
        
        # Draw version info
        painter.setFont(version_font)
        painter.drawText(30, 320, "Version 1.0.0")
        painter.drawText(30, 335, "© 2024 Professional Tools")
        
        # Draw loading indicator area (will be updated dynamically)
        painter.setPen(QPen(QColor(170, 170, 170)))
        painter.drawText(30, 280, "Initializing application...")
        
        painter.end()
        
        super().__init__(pixmap)
        
        # Setup modern splash screen properties
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # Progress tracking
        self.current_progress = 0
        self.current_message = "Initializing application..."
        
        # Connect progress signal
        self.progress_updated.connect(self.update_progress)
        
        # Create progress bar widget overlay
        self.setup_progress_overlay()
    
    def setup_progress_overlay(self):
        """Setup the progress bar overlay widget"""
        # Create a widget to hold the progress bar
        self.progress_widget = QWidget()
        self.progress_widget.setFixedSize(440, 60)
        self.progress_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        # Create layout for progress elements
        layout = QVBoxLayout(self.progress_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create progress bar with modern styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #D4AF37, stop:1 #B8860B);
                border-radius: 3px;
            }
        """)
        
        # Create status label
        self.status_label = QLabel("Initializing application...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: normal;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        
        # Position the progress widget at the bottom of splash screen
        self.progress_widget.setParent(self)
        self.progress_widget.move(30, 240)
        self.progress_widget.show()
    
    def update_progress(self, progress: int, message: str):
        """
        Update progress and message with modern styling
        
        Args:
            progress: Progress percentage (0-100)
            message: Status message to display
        """
        self.current_progress = progress
        self.current_message = message
        
        # Update progress bar
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(progress)
        
        # Update status message
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
        
        # Process events to update display
        QApplication.processEvents()
    
    def simulate_loading(self):
        """
        Simulate loading process with progress updates
        """
        loading_steps = [
            (5, "Initializing user interface..."),
            (15, "Loading configuration files..."),
            (25, "Connecting to database..."),
            (35, "Setting up core modules..."),
            (45, "Loading UI components..."),
            (55, "Initializing web scraper engine..."),
            (65, "Setting up AI client connection..."),
            (75, "Configuring email sender..."),
            (85, "Loading application state..."),
            (95, "Finalizing setup..."),
            (100, "Application ready!")
        ]
        
        for progress, message in loading_steps:
            self.progress_updated.emit(progress, message)
            time.sleep(0.15)  # Simulate work being done
    
    def show_with_progress(self):
        """Show splash screen and simulate loading"""
        self.show()
        QApplication.processEvents()
        
        # Start loading simulation
        QTimer.singleShot(100, self.simulate_loading)


class StartupProgressDialog(QWidget):
    """
    Alternative startup progress dialog for systems that don't support splash screens well
    """
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the progress dialog UI"""
        self.setWindowTitle("Loading Web Scraper Email Automation")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Title label
        title_label = QLabel("Web Scraper Email Automation")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2E7D32;
                margin: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                margin: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                margin: 10px;
            }
            QProgressBar::chunk {
                background-color: #2E7D32;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Center on screen
        self.center_on_screen()
    
    def center_on_screen(self):
        """Center the dialog on screen"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def update_progress(self, progress: int, message: str):
        """
        Update progress and message
        
        Args:
            progress: Progress percentage (0-100)
            message: Status message to display
        """
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        QApplication.processEvents()
    
    def show_loading_sequence(self):
        """Show the loading sequence"""
        self.show()
        QApplication.processEvents()
        
        loading_steps = [
            (10, "Loading configuration..."),
            (20, "Initializing database..."),
            (30, "Setting up core modules..."),
            (40, "Loading UI components..."),
            (50, "Initializing web scraper..."),
            (60, "Setting up AI client..."),
            (70, "Configuring email sender..."),
            (80, "Loading application state..."),
            (90, "Finalizing setup..."),
            (100, "Ready!")
        ]
        
        for progress, message in loading_steps:
            self.update_progress(progress, message)
            time.sleep(0.1)  # Brief pause for each step
        
        # Keep visible for a moment before closing
        time.sleep(0.5)
        self.close()


# Alias for backward compatibility
SplashScreen = ModernSplashScreen

def show_startup_progress():
    """
    Show startup progress using the modern splash screen
    
    Returns:
        Progress dialog instance
    """
    try:
        # Use modern splash screen
        splash = ModernSplashScreen()
        splash.show_with_progress()
        return splash
    except Exception:
        # Fallback to progress dialog
        progress_dialog = StartupProgressDialog()
        progress_dialog.show_loading_sequence()
        return progress_dialog