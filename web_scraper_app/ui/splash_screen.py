"""
Splash screen for application startup
Shows loading progress and application information
"""

from PyQt6.QtWidgets import (
    QSplashScreen, QLabel, QProgressBar, QVBoxLayout, 
    QWidget, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPen
import time


class SplashScreen(QSplashScreen):
    """
    Custom splash screen with progress bar and status messages
    """
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    
    def __init__(self):
        # Create a simple pixmap for the splash screen
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor(46, 125, 50))  # Green background
        
        # Draw application info on pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up fonts
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        subtitle_font = QFont("Arial", 12)
        
        # Draw title
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(title_font)
        painter.drawText(20, 50, "Web Scraper Email Automation")
        
        # Draw subtitle
        painter.setFont(subtitle_font)
        painter.drawText(20, 80, "Professional Email Outreach Tool")
        
        # Draw version
        painter.drawText(20, 260, "Version 1.0.0")
        painter.drawText(20, 280, "Loading...")
        
        painter.end()
        
        super().__init__(pixmap)
        
        # Setup splash screen properties
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Progress tracking
        self.current_progress = 0
        self.current_message = "Initializing..."
        
        # Connect progress signal
        self.progress_updated.connect(self.update_progress)
    
    def update_progress(self, progress: int, message: str):
        """
        Update progress and message
        
        Args:
            progress: Progress percentage (0-100)
            message: Status message to display
        """
        self.current_progress = progress
        self.current_message = message
        
        # Update the splash screen message
        self.showMessage(
            f"{message}\n{progress}%",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
            QColor(255, 255, 255)
        )
        
        # Process events to update display
        QApplication.processEvents()
    
    def simulate_loading(self):
        """
        Simulate loading process with progress updates
        """
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
            self.progress_updated.emit(progress, message)
            time.sleep(0.2)  # Simulate work being done
    
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


def show_startup_progress():
    """
    Show startup progress using the most appropriate method
    
    Returns:
        Progress dialog instance
    """
    try:
        # Try splash screen first
        splash = SplashScreen()
        splash.show_with_progress()
        return splash
    except Exception:
        # Fallback to progress dialog
        progress_dialog = StartupProgressDialog()
        progress_dialog.show_loading_sequence()
        return progress_dialog