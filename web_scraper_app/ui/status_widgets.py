"""
Custom status and indicator widgets for enhanced user experience
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton,
    QProgressBar, QFrame, QToolTip, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QIcon
import time
from typing import Optional


class StatusIndicator(QLabel):
    """
    Enhanced status indicator with animations and tooltips
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, text: str = "Ready", status_type: str = "neutral"):
        super().__init__(text)
        self.status_type = status_type
        self.is_animated = False
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_pulse)
        self.pulse_opacity = 1.0
        self.pulse_direction = -1
        
        self.setup_ui()
        self.set_status_type(status_type)
    
    def setup_ui(self):
        """Setup the status indicator UI"""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(24)
        self.setStyleSheet("""
            QLabel {
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def set_status_type(self, status_type: str):
        """
        Set the status type and update appearance
        
        Args:
            status_type: Type of status (success, error, warning, info, neutral, loading)
        """
        self.status_type = status_type
        
        colors = {
            'success': {'bg': '#4CAF50', 'text': '#FFFFFF'},
            'error': {'bg': '#F44336', 'text': '#FFFFFF'},
            'warning': {'bg': '#FF9800', 'text': '#FFFFFF'},
            'info': {'bg': '#1976D2', 'text': '#FFFFFF'},
            'neutral': {'bg': '#616161', 'text': '#FFFFFF'},
            'loading': {'bg': '#1976D2', 'text': '#FFFFFF'}
        }
        
        color_scheme = colors.get(status_type, colors['neutral'])
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color_scheme['bg']};
                color: {color_scheme['text']};
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 11px;
            }}
            QLabel:hover {{
                background-color: {self.lighten_color(color_scheme['bg'])};
            }}
        """)
        
        # Start animation for loading status
        if status_type == 'loading':
            self.start_pulse_animation()
        else:
            self.stop_pulse_animation()
    
    def lighten_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Lighten a hex color by a factor"""
        color = QColor(hex_color)
        h, s, l, a = color.getHsl()
        l = min(255, int(l + (255 - l) * factor))
        color.setHsl(h, s, l, a)
        return color.name()
    
    def start_pulse_animation(self):
        """Start pulse animation for loading states"""
        if not self.is_animated:
            self.is_animated = True
            self.animation_timer.start(50)  # 50ms intervals
    
    def stop_pulse_animation(self):
        """Stop pulse animation"""
        if self.is_animated:
            self.is_animated = False
            self.animation_timer.stop()
            self.setStyleSheet(self.styleSheet())  # Reset opacity
    
    def animate_pulse(self):
        """Animate the pulse effect"""
        self.pulse_opacity += self.pulse_direction * 0.05
        
        if self.pulse_opacity <= 0.3:
            self.pulse_direction = 1
        elif self.pulse_opacity >= 1.0:
            self.pulse_direction = -1
        
        # Apply opacity to the widget
        self.setWindowOpacity(self.pulse_opacity)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_status(self, text: str, status_type: str, tooltip: Optional[str] = None):
        """
        Update status text, type, and tooltip
        
        Args:
            text: Status text to display
            status_type: Type of status
            tooltip: Optional tooltip text
        """
        self.setText(text)
        self.set_status_type(status_type)
        
        if tooltip:
            self.setToolTip(tooltip)


class ProgressIndicator(QWidget):
    """
    Enhanced progress indicator with status text and animations
    """
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.is_visible = False
    
    def setup_ui(self):
        """Setup the progress indicator UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #66BB6A);
                border-radius: 6px;
            }
        """)
        self.progress_bar.setMinimumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Initially hidden
        self.setVisible(False)
    
    def show_progress(self, message: str, progress: int = -1):
        """
        Show progress with message
        
        Args:
            message: Status message to display
            progress: Progress value (0-100, -1 for indeterminate)
        """
        self.status_label.setText(message)
        
        if progress >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
        else:
            # Indeterminate progress
            self.progress_bar.setRange(0, 0)
        
        if not self.is_visible:
            self.setVisible(True)
            self.is_visible = True
    
    def hide_progress(self):
        """Hide the progress indicator"""
        if self.is_visible:
            self.setVisible(False)
            self.is_visible = False
    
    def update_progress(self, message: str, progress: int):
        """
        Update progress and message
        
        Args:
            message: New status message
            progress: New progress value
        """
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)


class ConnectionStatusWidget(QWidget):
    """
    Widget showing connection status for multiple services
    """
    
    test_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service_indicators = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the connection status widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)
        
        # Connection status label
        status_label = QLabel("Connections:")
        status_label.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(status_label)
        
        # Service indicators
        services = ['Gemini AI', 'SMTP']
        for service in services:
            indicator = StatusIndicator("●", "neutral")
            indicator.setMinimumWidth(60)
            indicator.setToolTip(f"{service} connection status")
            indicator.clicked.connect(self.test_requested.emit)
            
            self.service_indicators[service] = indicator
            layout.addWidget(indicator)
        
        # Test button
        test_btn = QPushButton("Test")
        test_btn.setMaximumWidth(50)
        test_btn.setMaximumHeight(20)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        test_btn.clicked.connect(self.test_requested.emit)
        layout.addWidget(test_btn)
        
        layout.addStretch()
    
    def update_service_status(self, service: str, connected: bool, message: str = ""):
        """
        Update the status of a specific service
        
        Args:
            service: Service name ('Gemini AI' or 'SMTP')
            connected: Whether the service is connected
            message: Optional status message
        """
        if service in self.service_indicators:
            indicator = self.service_indicators[service]
            
            if connected:
                indicator.update_status("●", "success", f"{service}: Connected\n{message}")
            else:
                indicator.update_status("●", "error", f"{service}: Disconnected\n{message}")
    
    def set_testing_status(self, service: str):
        """
        Set a service to testing status
        
        Args:
            service: Service name to set as testing
        """
        if service in self.service_indicators:
            indicator = self.service_indicators[service]
            indicator.update_status("●", "loading", f"{service}: Testing connection...")


class NotificationBanner(QFrame):
    """
    Notification banner for important messages
    """
    
    dismissed = pyqtSignal()
    
    def __init__(self, message: str, notification_type: str = "info", auto_dismiss: int = 0):
        super().__init__()
        self.notification_type = notification_type
        self.auto_dismiss_timer = QTimer()
        self.auto_dismiss_timer.timeout.connect(self.dismiss)
        
        self.setup_ui(message)
        
        if auto_dismiss > 0:
            self.auto_dismiss_timer.start(auto_dismiss * 1000)  # Convert to milliseconds
    
    def setup_ui(self, message: str):
        """Setup the notification banner UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Icon based on type
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        
        icon_label = QLabel(icons.get(self.notification_type, 'ℹ️'))
        icon_label.setFont(QFont("Arial", 14))
        layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 12px; color: #333;")
        layout.addWidget(message_label)
        
        layout.addStretch()
        
        # Dismiss button
        dismiss_btn = QPushButton("×")
        dismiss_btn.setMaximumSize(20, 20)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #666;
            }
            QPushButton:hover {
                color: #333;
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
        """)
        dismiss_btn.clicked.connect(self.dismiss)
        layout.addWidget(dismiss_btn)
        
        # Style based on type
        colors = {
            'info': '#E3F2FD',
            'success': '#E8F5E8',
            'warning': '#FFF3E0',
            'error': '#FFEBEE'
        }
        
        bg_color = colors.get(self.notification_type, colors['info'])
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {self.darken_color(bg_color)};
                border-radius: 8px;
                margin: 2px;
            }}
        """)
    
    def darken_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Darken a hex color by a factor"""
        color = QColor(hex_color)
        h, s, l, a = color.getHsl()
        l = max(0, int(l - l * factor))
        color.setHsl(h, s, l, a)
        return color.name()
    
    def dismiss(self):
        """Dismiss the notification"""
        self.auto_dismiss_timer.stop()
        self.hide()
        self.dismissed.emit()


class ActivityIndicator(QLabel):
    """
    Simple activity indicator showing current application activity
    """
    
    def __init__(self):
        super().__init__("Ready")
        self.activity_history = []
        self.max_history = 5
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the activity indicator UI"""
        self.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                padding: 2px 8px;
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 3px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    
    def update_activity(self, activity: str):
        """
        Update current activity
        
        Args:
            activity: Description of current activity
        """
        self.setText(activity)
        
        # Add to history
        timestamp = time.strftime("%H:%M:%S")
        self.activity_history.append(f"{timestamp}: {activity}")
        
        # Limit history size
        if len(self.activity_history) > self.max_history:
            self.activity_history = self.activity_history[-self.max_history:]
        
        # Update tooltip with history
        history_text = "Recent Activity:\n" + "\n".join(self.activity_history)
        self.setToolTip(history_text)