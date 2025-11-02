"""
Settings tab for API configuration and SMTP settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QLineEdit, QSpinBox, QCheckBox, QGroupBox,
    QMessageBox, QFileDialog, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont
import json
from pathlib import Path
from typing import Optional

from models.email_model import SMTPConfig
from core.config_manager import ConfigManager, ConfigurationError


class ConnectionTestWorker(QThread):
    """Worker thread for testing connections without blocking UI"""
    
    test_completed = pyqtSignal(str, bool, str)  # test_type, success, message
    
    def __init__(self, config_manager: ConfigManager, test_type: str):
        super().__init__()
        self.config_manager = config_manager
        self.test_type = test_type
    
    def run(self):
        """Run the connection test"""
        try:
            if self.test_type == "gemini":
                success, message = self.config_manager.test_gemini_connection()
            elif self.test_type == "smtp":
                success, message = self.config_manager.test_smtp_connection()
            else:
                success, message = False, "Unknown test type"
            
            self.test_completed.emit(self.test_type, success, message)
        except Exception as e:
            self.test_completed.emit(self.test_type, False, f"Test failed: {str(e)}")


class SettingsTab(QWidget):
    """Settings tab for API keys, SMTP configuration, and application preferences"""
    
    # Signals
    configuration_changed = pyqtSignal()
    test_connection_requested = pyqtSignal(str)  # test_type
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.test_worker = None
        self.setup_ui()
        self.load_current_settings()
        self.connect_signals()
    
    def setup_ui(self):
        """Initialize the settings UI with proper scrolling"""
        # Set the tab content class for styling
        self.setProperty("class", "tab-content")
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        content_widget.setProperty("class", "tab-content")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(25)
        
        # Title
        title_label = QLabel("Settings & Configuration")
        title_label.setProperty("class", "title")
        content_layout.addWidget(title_label)
        
        # API Configuration Section
        self.setup_api_section(content_layout)
        
        # SMTP Configuration Section
        self.setup_smtp_section(content_layout)
        
        # Application Preferences Section
        self.setup_preferences_section(content_layout)
        
        # Action buttons
        self.setup_action_buttons(content_layout)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
    
    def setup_api_section(self, parent_layout):
        """Setup API configuration section"""
        api_group = QGroupBox("Gemini AI Configuration")
        api_layout = QGridLayout(api_group)
        api_layout.setSpacing(10)
        
        # API Key input
        api_layout.addWidget(QLabel("API Key:"), 0, 0)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your Gemini API key")
        api_layout.addWidget(self.api_key_input, 0, 1)
        
        # Show/Hide API key button
        self.show_api_key_btn = QPushButton("Show")
        self.show_api_key_btn.setProperty("class", "secondary")
        self.show_api_key_btn.setMaximumWidth(60)
        api_layout.addWidget(self.show_api_key_btn, 0, 2)
        
        # Test connection button
        self.test_gemini_btn = QPushButton("Test Connection")
        self.test_gemini_btn.setProperty("class", "secondary")
        api_layout.addWidget(self.test_gemini_btn, 1, 0)
        
        # Connection status
        self.gemini_status_label = QLabel("Not configured")
        self.gemini_status_label.setProperty("class", "error")
        api_layout.addWidget(self.gemini_status_label, 1, 1)
        
        # Progress bar for testing
        self.gemini_progress = QProgressBar()
        self.gemini_progress.setVisible(False)
        self.gemini_progress.setRange(0, 0)  # Indeterminate progress
        api_layout.addWidget(self.gemini_progress, 1, 2)
        
        # Save API key button
        self.save_api_btn = QPushButton("Save API Key")
        api_layout.addWidget(self.save_api_btn, 2, 0)
        
        # Clear API key button
        self.clear_api_btn = QPushButton("Clear API Key")
        self.clear_api_btn.setProperty("class", "danger")
        api_layout.addWidget(self.clear_api_btn, 2, 1)
        
        parent_layout.addWidget(api_group)
    
    def setup_smtp_section(self, parent_layout):
        """Setup SMTP configuration section"""
        smtp_group = QGroupBox("SMTP Email Configuration")
        smtp_layout = QGridLayout(smtp_group)
        smtp_layout.setSpacing(10)
        
        # SMTP Server
        smtp_layout.addWidget(QLabel("SMTP Server:"), 0, 0)
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("e.g., smtp.gmail.com")
        smtp_layout.addWidget(self.smtp_server_input, 0, 1)
        
        # SMTP Port
        smtp_layout.addWidget(QLabel("Port:"), 0, 2)
        self.smtp_port_input = QSpinBox()
        self.smtp_port_input.setRange(1, 65535)
        self.smtp_port_input.setValue(587)
        smtp_layout.addWidget(self.smtp_port_input, 0, 3)
        
        # Email address
        smtp_layout.addWidget(QLabel("Email Address:"), 1, 0)
        self.smtp_email_input = QLineEdit()
        self.smtp_email_input.setPlaceholderText("your.email@example.com")
        smtp_layout.addWidget(self.smtp_email_input, 1, 1, 1, 3)
        
        # Password
        smtp_layout.addWidget(QLabel("Password:"), 2, 0)
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_password_input.setPlaceholderText("Email password or app password")
        smtp_layout.addWidget(self.smtp_password_input, 2, 1, 1, 2)
        
        # Show/Hide password button
        self.show_password_btn = QPushButton("Show")
        self.show_password_btn.setProperty("class", "secondary")
        self.show_password_btn.setMaximumWidth(60)
        smtp_layout.addWidget(self.show_password_btn, 2, 3)
        
        # Use TLS checkbox
        self.use_tls_checkbox = QCheckBox("Use TLS/STARTTLS")
        self.use_tls_checkbox.setChecked(True)
        smtp_layout.addWidget(self.use_tls_checkbox, 3, 0, 1, 2)
        
        # Test SMTP button
        self.test_smtp_btn = QPushButton("Test SMTP")
        self.test_smtp_btn.setProperty("class", "secondary")
        smtp_layout.addWidget(self.test_smtp_btn, 4, 0)
        
        # SMTP status
        self.smtp_status_label = QLabel("Not configured")
        self.smtp_status_label.setProperty("class", "error")
        smtp_layout.addWidget(self.smtp_status_label, 4, 1)
        
        # Progress bar for SMTP testing
        self.smtp_progress = QProgressBar()
        self.smtp_progress.setVisible(False)
        self.smtp_progress.setRange(0, 0)  # Indeterminate progress
        smtp_layout.addWidget(self.smtp_progress, 4, 2, 1, 2)
        
        # Save SMTP button
        self.save_smtp_btn = QPushButton("Save SMTP Config")
        smtp_layout.addWidget(self.save_smtp_btn, 5, 0)
        
        # Clear SMTP button
        self.clear_smtp_btn = QPushButton("Clear SMTP Config")
        self.clear_smtp_btn.setProperty("class", "danger")
        smtp_layout.addWidget(self.clear_smtp_btn, 5, 1)
        
        parent_layout.addWidget(smtp_group)
    
    def setup_preferences_section(self, parent_layout):
        """Setup application preferences section"""
        prefs_group = QGroupBox("Application Preferences")
        prefs_layout = QGridLayout(prefs_group)
        prefs_layout.setSpacing(10)
        
        # Configuration status
        prefs_layout.addWidget(QLabel("Configuration Status:"), 0, 0)
        self.config_status_label = QLabel("Checking...")
        prefs_layout.addWidget(self.config_status_label, 0, 1)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        prefs_layout.addWidget(line, 1, 0, 1, 4)
        
        # Export configuration
        self.export_config_btn = QPushButton("Export Configuration")
        self.export_config_btn.setProperty("class", "secondary")
        prefs_layout.addWidget(self.export_config_btn, 2, 0)
        
        # Import configuration
        self.import_config_btn = QPushButton("Import Configuration")
        self.import_config_btn.setProperty("class", "secondary")
        prefs_layout.addWidget(self.import_config_btn, 2, 1)
        
        # Validate all configurations
        self.validate_all_btn = QPushButton("Validate All Settings")
        prefs_layout.addWidget(self.validate_all_btn, 3, 0)
        
        # Clear all configurations
        self.clear_all_btn = QPushButton("Clear All Settings")
        self.clear_all_btn.setProperty("class", "danger")
        prefs_layout.addWidget(self.clear_all_btn, 3, 1)
        
        parent_layout.addWidget(prefs_group)
    
    def setup_action_buttons(self, parent_layout):
        """Setup action buttons at the bottom"""
        button_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Settings")
        self.refresh_btn.setProperty("class", "secondary")
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        # Gmail setup button
        self.gmail_setup_btn = QPushButton("Gmail Setup Guide")
        self.gmail_setup_btn.setProperty("class", "secondary")
        button_layout.addWidget(self.gmail_setup_btn)
        
        # Help button
        self.help_btn = QPushButton("Help")
        self.help_btn.setProperty("class", "secondary")
        button_layout.addWidget(self.help_btn)
        
        parent_layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect UI signals to handlers"""
        # API section signals
        self.show_api_key_btn.clicked.connect(self.toggle_api_key_visibility)
        self.test_gemini_btn.clicked.connect(self.test_gemini_connection)
        self.save_api_btn.clicked.connect(self.save_api_key)
        self.clear_api_btn.clicked.connect(self.clear_api_key)
        
        # SMTP section signals
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        self.test_smtp_btn.clicked.connect(self.test_smtp_connection)
        self.save_smtp_btn.clicked.connect(self.save_smtp_config)
        self.clear_smtp_btn.clicked.connect(self.clear_smtp_config)
        
        # Preferences section signals
        self.export_config_btn.clicked.connect(self.export_configuration)
        self.import_config_btn.clicked.connect(self.import_configuration)
        self.validate_all_btn.clicked.connect(self.validate_all_settings)
        self.clear_all_btn.clicked.connect(self.clear_all_settings)
        
        # Action buttons
        self.refresh_btn.clicked.connect(self.load_current_settings)
        self.gmail_setup_btn.clicked.connect(self.show_gmail_setup)
        self.help_btn.clicked.connect(self.show_help)
    
    def load_current_settings(self):
        """Load current settings from config manager"""
        try:
            # Load API key status
            api_key = self.config_manager.get_gemini_api_key()
            if api_key:
                self.api_key_input.setText("*" * 20)  # Show masked key
                self.gemini_status_label.setText("✓ API key configured")
                self.gemini_status_label.setProperty("class", "success")
            else:
                self.api_key_input.clear()
                self.gemini_status_label.setText("✗ No API key")
                self.gemini_status_label.setProperty("class", "error")
            
            # Load SMTP configuration
            smtp_config = self.config_manager.get_smtp_config()
            if smtp_config:
                self.smtp_server_input.setText(smtp_config.server)
                self.smtp_port_input.setValue(smtp_config.port)
                self.smtp_email_input.setText(smtp_config.email)
                self.smtp_password_input.setText("*" * 12)  # Show masked password
                self.use_tls_checkbox.setChecked(smtp_config.use_tls)
                self.smtp_status_label.setText("✓ SMTP configured")
                self.smtp_status_label.setProperty("class", "success")
            else:
                self.smtp_server_input.clear()
                self.smtp_port_input.setValue(587)
                self.smtp_email_input.clear()
                self.smtp_password_input.clear()
                self.use_tls_checkbox.setChecked(True)
                self.smtp_status_label.setText("✗ Not configured")
                self.smtp_status_label.setProperty("class", "error")
            
            # Update configuration status
            self.update_configuration_status()
            
            # Refresh styles
            self.style().unpolish(self.gemini_status_label)
            self.style().polish(self.gemini_status_label)
            self.style().unpolish(self.smtp_status_label)
            self.style().polish(self.smtp_status_label)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings: {str(e)}")
    
    def update_configuration_status(self):
        """Update the overall configuration status"""
        status = self.config_manager.get_configuration_status()
        
        if status["fully_configured"]:
            self.config_status_label.setText("✓ Fully configured")
            self.config_status_label.setProperty("class", "success")
        elif status["gemini_configured"] or status["smtp_configured"]:
            self.config_status_label.setText("⚠ Partially configured")
            self.config_status_label.setProperty("class", "error")
        else:
            self.config_status_label.setText("✗ Not configured")
            self.config_status_label.setProperty("class", "error")
        
        # Refresh style
        self.style().unpolish(self.config_status_label)
        self.style().polish(self.config_status_label)  
  
    # API Configuration Methods
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_api_key_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_api_key_btn.setText("Show")
    
    def test_gemini_connection(self):
        """Test Gemini API connection"""
        api_key = self.api_key_input.text().strip()
        if not api_key or api_key.startswith("*"):
            # If no key entered or showing masked key, use stored key
            stored_key = self.config_manager.get_gemini_api_key()
            if not stored_key:
                QMessageBox.warning(self, "No API Key", "Please enter a Gemini API key first.")
                return
        else:
            # Temporarily save the entered key for testing
            try:
                self.config_manager.set_gemini_api_key(api_key)
            except ConfigurationError as e:
                QMessageBox.critical(self, "Error", f"Failed to save API key: {str(e)}")
                return
        
        # Start connection test
        self.test_gemini_btn.setEnabled(False)
        self.gemini_progress.setVisible(True)
        self.gemini_status_label.setText("Testing connection...")
        
        # Create and start worker thread
        self.test_worker = ConnectionTestWorker(self.config_manager, "gemini")
        self.test_worker.test_completed.connect(self.on_gemini_test_completed)
        self.test_worker.start()
    
    @pyqtSlot(str, bool, str)
    def on_gemini_test_completed(self, test_type, success, message):
        """Handle Gemini connection test completion"""
        if test_type == "gemini":
            self.test_gemini_btn.setEnabled(True)
            self.gemini_progress.setVisible(False)
            
            if success:
                self.gemini_status_label.setText(f"✓ {message}")
                self.gemini_status_label.setProperty("class", "success")
                QMessageBox.information(self, "Connection Test", f"Gemini API: {message}")
            else:
                self.gemini_status_label.setText(f"✗ {message}")
                self.gemini_status_label.setProperty("class", "error")
                QMessageBox.warning(self, "Connection Test Failed", f"Gemini API: {message}")
            
            # Refresh style
            self.style().unpolish(self.gemini_status_label)
            self.style().polish(self.gemini_status_label)
            self.update_configuration_status()
    
    def save_api_key(self):
        """Save Gemini API key"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid API key.")
            return
        
        if api_key.startswith("*"):
            QMessageBox.information(self, "No Changes", "API key is already saved.")
            return
        
        try:
            self.config_manager.set_gemini_api_key(api_key)
            self.api_key_input.setText("*" * 20)  # Mask the key
            self.gemini_status_label.setText("✓ API key saved")
            self.gemini_status_label.setProperty("class", "success")
            
            # Refresh style
            self.style().unpolish(self.gemini_status_label)
            self.style().polish(self.gemini_status_label)
            self.update_configuration_status()
            
            QMessageBox.information(self, "Success", "Gemini API key saved successfully!")
            self.configuration_changed.emit()
            
        except ConfigurationError as e:
            QMessageBox.critical(self, "Error", f"Failed to save API key: {str(e)}")
    
    def clear_api_key(self):
        """Clear Gemini API key"""
        reply = QMessageBox.question(
            self,
            "Clear API Key",
            "Are you sure you want to clear the Gemini API key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.clear_gemini_config()
                self.api_key_input.clear()
                self.gemini_status_label.setText("✗ No API key")
                self.gemini_status_label.setProperty("class", "error")
                
                # Refresh style
                self.style().unpolish(self.gemini_status_label)
                self.style().polish(self.gemini_status_label)
                self.update_configuration_status()
                
                QMessageBox.information(self, "Success", "Gemini API key cleared successfully!")
                self.configuration_changed.emit()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear API key: {str(e)}")
    
    # SMTP Configuration Methods
    def toggle_password_visibility(self):
        """Toggle SMTP password visibility"""
        if self.smtp_password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("Hide")
        else:
            self.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("Show")
    
    def test_smtp_connection(self):
        """Test SMTP connection"""
        # Validate inputs
        server = self.smtp_server_input.text().strip()
        port = self.smtp_port_input.value()
        email = self.smtp_email_input.text().strip()
        password = self.smtp_password_input.text().strip()
        
        if not all([server, email, password]):
            QMessageBox.warning(self, "Invalid Input", "Please fill in all SMTP fields.")
            return
        
        # Create SMTP config
        smtp_config = SMTPConfig(
            server=server,
            port=port,
            email=email,
            password=password,
            use_tls=self.use_tls_checkbox.isChecked()
        )
        
        # Save temporarily for testing
        try:
            self.config_manager.set_smtp_config(smtp_config)
        except ConfigurationError as e:
            QMessageBox.critical(self, "Error", f"Failed to save SMTP config: {str(e)}")
            return
        
        # Start connection test
        self.test_smtp_btn.setEnabled(False)
        self.smtp_progress.setVisible(True)
        self.smtp_status_label.setText("Testing connection...")
        
        # Create and start worker thread
        self.test_worker = ConnectionTestWorker(self.config_manager, "smtp")
        self.test_worker.test_completed.connect(self.on_smtp_test_completed)
        self.test_worker.start()
    
    @pyqtSlot(str, bool, str)
    def on_smtp_test_completed(self, test_type, success, message):
        """Handle SMTP connection test completion"""
        if test_type == "smtp":
            self.test_smtp_btn.setEnabled(True)
            self.smtp_progress.setVisible(False)
            
            if success:
                self.smtp_status_label.setText(f"✓ {message}")
                self.smtp_status_label.setProperty("class", "success")
                QMessageBox.information(self, "Connection Test", f"SMTP: {message}")
            else:
                self.smtp_status_label.setText(f"✗ {message}")
                self.smtp_status_label.setProperty("class", "error")
                QMessageBox.warning(self, "Connection Test Failed", f"SMTP: {message}")
            
            # Refresh style
            self.style().unpolish(self.smtp_status_label)
            self.style().polish(self.smtp_status_label)
            self.update_configuration_status()
    
    def save_smtp_config(self):
        """Save SMTP configuration"""
        # Validate inputs
        server = self.smtp_server_input.text().strip()
        port = self.smtp_port_input.value()
        email = self.smtp_email_input.text().strip()
        password = self.smtp_password_input.text().strip()
        
        if not all([server, email, password]):
            QMessageBox.warning(self, "Invalid Input", "Please fill in all SMTP fields.")
            return
        
        if password.startswith("*"):
            QMessageBox.information(self, "No Changes", "SMTP configuration is already saved.")
            return
        
        # Create SMTP config
        smtp_config = SMTPConfig(
            server=server,
            port=port,
            email=email,
            password=password,
            use_tls=self.use_tls_checkbox.isChecked()
        )
        
        try:
            self.config_manager.set_smtp_config(smtp_config)
            self.smtp_password_input.setText("*" * 12)  # Mask the password
            self.smtp_status_label.setText("✓ SMTP configured")
            self.smtp_status_label.setProperty("class", "success")
            
            # Refresh style
            self.style().unpolish(self.smtp_status_label)
            self.style().polish(self.smtp_status_label)
            self.update_configuration_status()
            
            QMessageBox.information(self, "Success", "SMTP configuration saved successfully!")
            self.configuration_changed.emit()
            
        except ConfigurationError as e:
            QMessageBox.critical(self, "Error", f"Failed to save SMTP configuration: {str(e)}")
    
    def clear_smtp_config(self):
        """Clear SMTP configuration"""
        reply = QMessageBox.question(
            self,
            "Clear SMTP Configuration",
            "Are you sure you want to clear the SMTP configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.clear_smtp_config()
                self.smtp_server_input.clear()
                self.smtp_port_input.setValue(587)
                self.smtp_email_input.clear()
                self.smtp_password_input.clear()
                self.use_tls_checkbox.setChecked(True)
                self.smtp_status_label.setText("✗ Not configured")
                self.smtp_status_label.setProperty("class", "error")
                
                # Refresh style
                self.style().unpolish(self.smtp_status_label)
                self.style().polish(self.smtp_status_label)
                self.update_configuration_status()
                
                QMessageBox.information(self, "Success", "SMTP configuration cleared successfully!")
                self.configuration_changed.emit()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear SMTP configuration: {str(e)}")
    
    # Application Preferences Methods
    def export_configuration(self):
        """Export configuration to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration",
            "web_scraper_config.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Get non-sensitive configuration data
                config_data = {
                    "smtp_server": self.smtp_server_input.text(),
                    "smtp_port": self.smtp_port_input.value(),
                    "smtp_email": self.smtp_email_input.text(),
                    "smtp_use_tls": self.use_tls_checkbox.isChecked(),
                    "gemini_api_configured": bool(self.config_manager.get_gemini_api_key()),
                    "smtp_configured": bool(self.config_manager.get_smtp_config()),
                    "export_timestamp": str(Path().cwd()),
                    "note": "This export does not include sensitive data like passwords or API keys"
                }
                
                with open(file_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Configuration exported to:\n{file_path}\n\n"
                    "Note: Sensitive data (passwords, API keys) are not included."
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export configuration: {str(e)}")
    
    def import_configuration(self):
        """Import configuration from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Configuration",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
                
                # Import non-sensitive settings
                if "smtp_server" in config_data:
                    self.smtp_server_input.setText(config_data["smtp_server"])
                if "smtp_port" in config_data:
                    self.smtp_port_input.setValue(config_data["smtp_port"])
                if "smtp_email" in config_data:
                    self.smtp_email_input.setText(config_data["smtp_email"])
                if "smtp_use_tls" in config_data:
                    self.use_tls_checkbox.setChecked(config_data["smtp_use_tls"])
                
                QMessageBox.information(
                    self, 
                    "Import Successful", 
                    f"Configuration imported from:\n{file_path}\n\n"
                    "Note: You will need to re-enter sensitive data (passwords, API keys)."
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Failed to import configuration: {str(e)}")
    
    def validate_all_settings(self):
        """Validate all configuration settings"""
        self.validate_all_btn.setEnabled(False)
        self.validate_all_btn.setText("Validating...")
        
        try:
            results = self.config_manager.validate_configuration()
            
            # Build result message
            message = "Configuration Validation Results:\n\n"
            
            gemini_success, gemini_msg = results.get("gemini", (False, "Not tested"))
            smtp_success, smtp_msg = results.get("smtp", (False, "Not tested"))
            
            message += f"Gemini AI: {'✓' if gemini_success else '✗'} {gemini_msg}\n"
            message += f"SMTP: {'✓' if smtp_success else '✗'} {smtp_msg}\n\n"
            
            if gemini_success and smtp_success:
                message += "All configurations are working properly!"
                QMessageBox.information(self, "Validation Results", message)
            else:
                message += "Some configurations need attention. Check the Settings tab for details."
                QMessageBox.warning(self, "Validation Results", message)
            
            # Update UI status
            self.load_current_settings()
            
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate settings: {str(e)}")
        
        finally:
            self.validate_all_btn.setEnabled(True)
            self.validate_all_btn.setText("Validate All Settings")
    
    def clear_all_settings(self):
        """Clear all configuration settings"""
        reply = QMessageBox.question(
            self,
            "Clear All Settings",
            "Are you sure you want to clear ALL configuration settings?\n\n"
            "This will remove:\n"
            "• Gemini API key\n"
            "• SMTP configuration\n"
            "• All saved preferences\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.clear_all_config()
                self.load_current_settings()  # Refresh UI
                
                QMessageBox.information(self, "Success", "All configuration settings cleared successfully!")
                self.configuration_changed.emit()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear settings: {str(e)}")
    
    def show_help(self):
        """Show help information"""
        help_text = """
<h3>Settings Help</h3>

<h4>Gemini AI Configuration:</h4>
<ul>
<li><b>API Key:</b> Get your API key from Google AI Studio (https://makersuite.google.com/app/apikey)</li>
<li><b>Test Connection:</b> Validates your API key and checks quota</li>
</ul>

<h4>SMTP Configuration:</h4>
<ul>
<li><b>Gmail:</b> Use smtp.gmail.com, port 587, and an App Password</li>
<li><b>Outlook:</b> Use smtp-mail.outlook.com, port 587</li>
<li><b>Yahoo:</b> Use smtp.mail.yahoo.com, port 587</li>
<li><b>Test SMTP:</b> Validates your email server connection</li>
</ul>

<h4>Security:</h4>
<ul>
<li>API keys and passwords are stored securely using system keyring</li>
<li>Configuration exports do not include sensitive data</li>
<li>Use App Passwords for Gmail (not your regular password)</li>
</ul>

<h4>Troubleshooting:</h4>
<ul>
<li>If tests fail, check your internet connection</li>
<li>For Gmail, enable 2FA and use App Passwords</li>
<li>Some email providers require "Less secure app access"</li>
</ul>
        """
        
        QMessageBox.information(self, "Settings Help", help_text)
    
    def show_gmail_setup(self):
        """Show Gmail setup instructions"""
        gmail_help = """
<h3>Gmail SMTP Setup Guide</h3>

<h4>🔧 Quick Setup Steps:</h4>
<ol>
<li><b>Enable 2-Factor Authentication</b> on your Google account</li>
<li><b>Generate App Password:</b> Google Account → Security → App Passwords → Mail</li>
<li><b>Configure below:</b>
   <ul>
   <li>Server: smtp.gmail.com</li>
   <li>Port: 587</li>
   <li>Email: your-email@gmail.com</li>
   <li>Password: 16-character App Password (not regular password)</li>
   <li>TLS: Enabled ✓</li>
   </ul>
</li>
<li><b>Test Connection</b> using the button below</li>
</ol>

<h4>⚠️ Important Notes:</h4>
<ul>
<li><b>Never use your regular Gmail password</b> - only App Passwords work</li>
<li><b>App Password looks like:</b> abcd efgh ijkl mnop (16 characters with spaces)</li>
<li><b>2FA must be enabled</b> before you can create App Passwords</li>
</ul>

<h4>❌ Common Errors:</h4>
<ul>
<li><b>"Authentication failed"</b> → Using wrong password (use App Password)</li>
<li><b>"Connection refused"</b> → Check server/port settings</li>
<li><b>"Too many attempts"</b> → Wait 15 minutes, then try again</li>
</ul>

<p><b>💡 Tip:</b> Fill in the settings below, then click "Test SMTP" to verify!</p>
        """
        
        QMessageBox.information(self, "Gmail Setup Guide", gmail_help)