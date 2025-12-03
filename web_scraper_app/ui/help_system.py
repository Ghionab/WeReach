"""
Comprehensive help system for the Web Scraper Email Automation Tool
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit,
    QLabel, QPushButton, QScrollArea, QWidget, QFrame, QListWidget,
    QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
from typing import Dict, List


class HelpDialog(QDialog):
    """
    Comprehensive help dialog with multiple sections
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Web Scraper Email Automation - Help")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.populate_content()
    
    def setup_ui(self):
        """Setup the help dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Web Scraper Email Automation Tool - Help")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2E7D32;
                padding: 10px;
                border-bottom: 2px solid #E0E0E0;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Create tab widget for different help sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def populate_content(self):
        """Populate help content in tabs"""
        # Getting Started tab
        self.add_getting_started_tab()
        
        # Keyboard Shortcuts tab
        self.add_keyboard_shortcuts_tab()
        
        # Features Guide tab
        self.add_features_guide_tab()
        
        # Troubleshooting tab
        self.add_troubleshooting_tab()
        
        # FAQ tab
        self.add_faq_tab()
        
        # About tab
        self.add_about_tab()
    
    def add_getting_started_tab(self):
        """Add getting started guide tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Getting Started Guide</h2>
        
        <h3>1. Initial Setup</h3>
        <p><strong>Configure API Keys and SMTP Settings:</strong></p>
        <ul>
        <li>Go to the <strong>Settings</strong> tab (Ctrl+4)</li>
        <li>Enter your <strong>Gemini AI API key</strong> in the API Configuration section</li>
        <li>Configure your <strong>SMTP settings</strong> for email sending</li>
        <li>Click <strong>"Test Connection"</strong> buttons to verify your settings</li>
        <li>Save your configurations</li>
        </ul>
        
        <h3>2. Scraping Websites</h3>
        <p><strong>Add URLs and Start Scraping:</strong></p>
        <ul>
        <li>Go to the <strong>Dashboard</strong> tab (Ctrl+1)</li>
        <li>Add website URLs manually or upload a CSV file</li>
        <li>Click <strong>"Start Scraping"</strong> (Ctrl+R) to begin</li>
        <li>Watch real-time progress and results</li>
        <li>Export results to CSV if needed (Ctrl+E)</li>
        </ul>
        
        <h3>3. Generating and Sending Emails</h3>
        <p><strong>Create AI-Powered Cold Emails:</strong></p>
        <ul>
        <li>Go to the <strong>Email</strong> tab (Ctrl+2)</li>
        <li>Click <strong>"Generate Cold Emails"</strong> (Ctrl+G)</li>
        <li>Review and edit generated emails</li>
        <li>Select emails to send using checkboxes</li>
        <li>Click <strong>"Send Selected Emails"</strong> (Ctrl+Shift+S)</li>
        </ul>
        
        <h3>4. Tracking Email History</h3>
        <p><strong>Monitor Your Email Campaigns:</strong></p>
        <ul>
        <li>Go to the <strong>History</strong> tab (Ctrl+3)</li>
        <li>View all sent emails with status information</li>
        <li>Search and filter email history</li>
        <li>Export email history for analysis</li>
        </ul>
        
        <div style="background-color: #E8F5E8; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4>💡 Quick Tips:</h4>
        <ul>
        <li>Use <strong>Ctrl+/</strong> to see all keyboard shortcuts</li>
        <li>The status bar shows connection status and recent activity</li>
        <li>Hover over buttons and fields for helpful tooltips</li>
        <li>Use <strong>F5</strong> to refresh the current tab</li>
        <li>Press <strong>Escape</strong> to stop running operations</li>
        </ul>
        </div>
        """)
        
        layout.addWidget(text)
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "🚀 Getting Started")
    
    def add_keyboard_shortcuts_tab(self):
        """Add keyboard shortcuts reference tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Keyboard Shortcuts Reference</h2>
        
        <h3>🧭 Navigation Shortcuts</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><strong>Ctrl+1</strong></td><td>Switch to Dashboard tab</td></tr>
        <tr><td><strong>Ctrl+2</strong></td><td>Switch to Email tab</td></tr>
        <tr><td><strong>Ctrl+3</strong></td><td>Switch to History tab</td></tr>
        <tr><td><strong>Ctrl+4</strong></td><td>Switch to Settings tab</td></tr>
        <tr><td><strong>Alt+Left</strong></td><td>Previous tab</td></tr>
        <tr><td><strong>Alt+Right</strong></td><td>Next tab</td></tr>
        <tr><td><strong>Ctrl+H</strong></td><td>Go to History tab</td></tr>
        </table>
        
        <h3>⚡ Action Shortcuts</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><strong>Ctrl+R</strong></td><td>Start scraping / Refresh current tab</td></tr>
        <tr><td><strong>Ctrl+G</strong></td><td>Generate emails</td></tr>
        <tr><td><strong>Ctrl+Shift+S</strong></td><td>Send emails</td></tr>
        <tr><td><strong>Ctrl+T</strong></td><td>Test API and SMTP connections</td></tr>
        <tr><td><strong>F5</strong></td><td>Refresh current tab</td></tr>
        <tr><td><strong>Escape</strong></td><td>Stop current operation</td></tr>
        </table>
        
        <h3>📁 File Operations</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><strong>Ctrl+I</strong></td><td>Import URLs from CSV</td></tr>
        <tr><td><strong>Ctrl+E</strong></td><td>Export data to CSV</td></tr>
        <tr><td><strong>Ctrl+Q</strong></td><td>Exit application</td></tr>
        </table>
        
        <h3>🛠️ Utility Shortcuts</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr><th>Shortcut</th><th>Action</th></tr>
        <tr><td><strong>Ctrl+N</strong></td><td>Focus URL input field</td></tr>
        <tr><td><strong>Ctrl+D</strong></td><td>Clear (context-dependent)</td></tr>
        <tr><td><strong>Ctrl+/</strong></td><td>Show keyboard shortcuts help</td></tr>
        <tr><td><strong>F1</strong></td><td>Show documentation</td></tr>
        </table>
        
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4>⚠️ Context-Dependent Actions:</h4>
        <p><strong>Ctrl+D (Clear)</strong> behavior depends on current tab:</p>
        <ul>
        <li><strong>Dashboard:</strong> Clear URL input or scraping results</li>
        <li><strong>Email:</strong> Deselect all emails</li>
        <li><strong>History:</strong> Clear search filters</li>
        <li><strong>Settings:</strong> Use individual clear buttons</li>
        </ul>
        </div>
        """)
        
        layout.addWidget(text)
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "⌨️ Shortcuts")
    
    def add_features_guide_tab(self):
        """Add detailed features guide tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Features Guide</h2>
        
        <h3>🏠 Dashboard Features</h3>
        <h4>URL Management:</h4>
        <ul>
        <li><strong>Manual URL Entry:</strong> Type URLs directly and press Enter</li>
        <li><strong>CSV Import:</strong> Upload CSV files with multiple URLs</li>
        <li><strong>URL Validation:</strong> Automatic validation of URL format</li>
        <li><strong>Duplicate Prevention:</strong> Prevents adding duplicate URLs</li>
        </ul>
        
        <h4>Web Scraping:</h4>
        <ul>
        <li><strong>Real-time Progress:</strong> Live progress bar and status updates</li>
        <li><strong>Email Extraction:</strong> Advanced regex pattern matching</li>
        <li><strong>Error Handling:</strong> Continues scraping even if some sites fail</li>
        <li><strong>Results Display:</strong> Real-time display of found emails</li>
        </ul>
        
        <h3>✉️ Email Features</h3>
        <h4>AI Email Generation:</h4>
        <ul>
        <li><strong>Gemini AI Integration:</strong> Uses Google's Gemini AI for content</li>
        <li><strong>Personalized Content:</strong> Tailored emails for each website</li>
        <li><strong>Professional Tone:</strong> Business-appropriate language</li>
        <li><strong>Editable Content:</strong> Modify generated emails before sending</li>
        </ul>
        
        <h4>Email Sending:</h4>
        <ul>
        <li><strong>Selective Sending:</strong> Choose which emails to send</li>
        <li><strong>Bulk Operations:</strong> Send multiple emails efficiently</li>
        <li><strong>Progress Tracking:</strong> Real-time sending progress</li>
        <li><strong>Error Reporting:</strong> Detailed success/failure reporting</li>
        </ul>
        
        <h3>📋 History Features</h3>
        <h4>Email Tracking:</h4>
        <ul>
        <li><strong>Complete History:</strong> All sent emails with timestamps</li>
        <li><strong>Status Tracking:</strong> Sent, Failed, Pending status</li>
        <li><strong>Search & Filter:</strong> Find specific emails quickly</li>
        <li><strong>Detailed View:</strong> Full email content display</li>
        </ul>
        
        <h4>Analytics:</h4>
        <ul>
        <li><strong>Statistics:</strong> Total, sent, failed, pending counts</li>
        <li><strong>Export Options:</strong> Export history for analysis</li>
        <li><strong>Real-time Updates:</strong> Automatic refresh after sending</li>
        </ul>
        
        <h3>⚙️ Settings Features</h3>
        <h4>API Configuration:</h4>
        <ul>
        <li><strong>Secure Storage:</strong> Encrypted API key storage</li>
        <li><strong>Connection Testing:</strong> Verify API connectivity</li>
        <li><strong>Visual Feedback:</strong> Clear status indicators</li>
        </ul>
        
        <h4>SMTP Configuration:</h4>
        <ul>
        <li><strong>Multiple Providers:</strong> Gmail, Outlook, custom SMTP</li>
        <li><strong>TLS Support:</strong> Secure email transmission</li>
        <li><strong>Connection Validation:</strong> Test before saving</li>
        <li><strong>Secure Credentials:</strong> Encrypted password storage</li>
        </ul>
        
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4>🔒 Security Features:</h4>
        <ul>
        <li><strong>Encrypted Storage:</strong> API keys and passwords are encrypted</li>
        <li><strong>Input Validation:</strong> Prevents malicious input</li>
        <li><strong>Secure Connections:</strong> TLS/SSL for all communications</li>
        <li><strong>No Data Sharing:</strong> All data stays on your computer</li>
        </ul>
        </div>
        """)
        
        layout.addWidget(text)
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "🎯 Features")
    
    def add_troubleshooting_tab(self):
        """Add troubleshooting guide tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Troubleshooting Guide</h2>
        
        <h3>🔧 Common Issues</h3>
        
        <h4>Connection Problems:</h4>
        <div style="background-color: #FFEBEE; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <strong>Problem:</strong> "Gemini AI connection failed"<br>
        <strong>Solutions:</strong>
        <ul>
        <li>Verify your API key is correct and active</li>
        <li>Check your internet connection</li>
        <li>Ensure you have Gemini API quota remaining</li>
        <li>Try regenerating your API key from Google AI Studio</li>
        </ul>
        </div>
        
        <div style="background-color: #FFEBEE; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <strong>Problem:</strong> "SMTP connection failed"<br>
        <strong>Solutions:</strong>
        <ul>
        <li>Verify server address and port number</li>
        <li>Check username and password</li>
        <li>Enable "Less secure app access" for Gmail</li>
        <li>Use app-specific passwords for 2FA accounts</li>
        <li>Verify TLS/SSL settings</li>
        </ul>
        </div>
        
        <h4>Scraping Issues:</h4>
        <div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <strong>Problem:</strong> "No emails found on website"<br>
        <strong>Solutions:</strong>
        <ul>
        <li>Check if the website actually contains email addresses</li>
        <li>Some websites may block automated scraping</li>
        <li>Try different pages of the same website</li>
        <li>Ensure the URL is accessible and loads properly</li>
        </ul>
        </div>
        
        <div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <strong>Problem:</strong> "Scraping is very slow"<br>
        <strong>Solutions:</strong>
        <ul>
        <li>Check your internet connection speed</li>
        <li>Some websites may have rate limiting</li>
        <li>Try scraping fewer URLs at once</li>
        <li>Restart the application if it becomes unresponsive</li>
        </ul>
        </div>
        
        <h4>Email Generation Issues:</h4>
        <div style="background-color: #E8F5E8; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <strong>Problem:</strong> "Email generation failed"<br>
        <strong>Solutions:</strong>
        <ul>
        <li>Verify Gemini AI connection is working</li>
        <li>Check if you have API quota remaining</li>
        <li>Try generating emails for fewer websites</li>
        <li>Wait a moment and try again (rate limiting)</li>
        </ul>
        </div>
        
        <h4>Email Sending Issues:</h4>
        <div style="background-color: #E3F2FD; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <strong>Problem:</strong> "Emails not sending"<br>
        <strong>Solutions:</strong>
        <ul>
        <li>Verify SMTP configuration is correct</li>
        <li>Check if recipient emails are valid</li>
        <li>Ensure you're not exceeding sending limits</li>
        <li>Check spam folder for test emails</li>
        <li>Try sending to a single recipient first</li>
        </ul>
        </div>
        
        <h3>🆘 Getting Help</h3>
        <p>If you continue to experience issues:</p>
        <ul>
        <li>Check the application logs for detailed error messages</li>
        <li>Try restarting the application</li>
        <li>Verify all your configurations in the Settings tab</li>
        <li>Test connections using the "Test Connection" buttons</li>
        <li>Make sure you have the latest version of the application</li>
        </ul>
        
        <div style="background-color: #F3E5F5; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4>📋 Diagnostic Information:</h4>
        <p>When reporting issues, please include:</p>
        <ul>
        <li>Operating system and version</li>
        <li>Application version</li>
        <li>Error messages (exact text)</li>
        <li>Steps to reproduce the problem</li>
        <li>Screenshots if applicable</li>
        </ul>
        </div>
        """)
        
        layout.addWidget(text)
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "🔧 Troubleshooting")
    
    def add_faq_tab(self):
        """Add FAQ tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Frequently Asked Questions</h2>
        
        <h3>General Questions</h3>
        
        <h4>Q: Is this application free to use?</h4>
        <p><strong>A:</strong> The application itself is free, but you need your own Gemini AI API key and SMTP email service. Google Gemini AI has free tier limits, and most email providers offer free SMTP access.</p>
        
        <h4>Q: Is my data secure?</h4>
        <p><strong>A:</strong> Yes, all data is stored locally on your computer. API keys and passwords are encrypted. No data is sent to external servers except for the AI API calls and email sending.</p>
        
        <h4>Q: Can I use this for commercial purposes?</h4>
        <p><strong>A:</strong> Please check the terms of service for your Gemini AI API and email provider. The application itself doesn't restrict commercial use.</p>
        
        <h3>Setup Questions</h3>
        
        <h4>Q: Where do I get a Gemini AI API key?</h4>
        <p><strong>A:</strong> Visit <a href="https://ai.google.dev/">Google AI Studio</a> to create a free account and generate an API key.</p>
        
        <h4>Q: What SMTP settings should I use for Gmail?</h4>
        <p><strong>A:</strong> 
        <ul>
        <li>Server: smtp.gmail.com</li>
        <li>Port: 587</li>
        <li>Use TLS: Yes</li>
        <li>Use an app-specific password if you have 2FA enabled</li>
        </ul>
        </p>
        
        <h4>Q: Can I use other email providers?</h4>
        <p><strong>A:</strong> Yes! The application supports any SMTP-compatible email service including Outlook, Yahoo, and custom SMTP servers.</p>
        
        <h3>Usage Questions</h3>
        
        <h4>Q: How many websites can I scrape at once?</h4>
        <p><strong>A:</strong> There's no hard limit, but performance depends on your internet connection and the websites' response times. Start with 10-20 URLs for best results.</p>
        
        <h4>Q: Can I customize the email templates?</h4>
        <p><strong>A:</strong> Yes! After generating emails, you can edit both the subject and body before sending. You can also modify the AI prompt by editing the source code.</p>
        
        <h4>Q: What email formats are detected?</h4>
        <p><strong>A:</strong> The application uses a comprehensive regex pattern that detects most standard email formats including international domains.</p>
        
        <h4>Q: Can I schedule emails to be sent later?</h4>
        <p><strong>A:</strong> Currently, the application sends emails immediately. Scheduling features may be added in future versions.</p>
        
        <h3>Technical Questions</h3>
        
        <h4>Q: What happens if scraping fails for some websites?</h4>
        <p><strong>A:</strong> The application continues scraping other websites and reports which ones failed. Failed sites are marked in the URL list.</p>
        
        <h4>Q: How are duplicate emails handled?</h4>
        <p><strong>A:</strong> The application automatically prevents duplicate emails from being stored in the database.</p>
        
        <h4>Q: Can I export my data?</h4>
        <p><strong>A:</strong> Yes! You can export scraped emails and email history to CSV format for use in other applications.</p>
        
        <h4>Q: What if I lose my configuration?</h4>
        <p><strong>A:</strong> You can export your configuration (excluding sensitive data) from the Settings tab and import it later.</p>
        
        <div style="background-color: #E8F5E8; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4>💡 Pro Tips:</h4>
        <ul>
        <li>Test with a small number of URLs first</li>
        <li>Always verify your SMTP settings before sending bulk emails</li>
        <li>Keep your API keys secure and don't share them</li>
        <li>Regularly export your data as backup</li>
        <li>Use keyboard shortcuts for faster workflow</li>
        </ul>
        </div>
        """)
        
        layout.addWidget(text)
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "❓ FAQ")
    
    def add_about_tab(self):
        """Add about tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <div style="text-align: center;">
        <h1>Web Scraper Email Automation Tool</h1>
        <h2>Version 1.0.0</h2>
        </div>
        
        <h3>About This Application</h3>
        <p>The Web Scraper Email Automation Tool is a professional desktop application designed to streamline your email outreach process. It combines powerful web scraping capabilities with AI-powered email generation to help you connect with potential clients and partners efficiently.</p>
        
        <h3>Key Features</h3>
        <ul>
        <li><strong>Intelligent Web Scraping:</strong> Extract email addresses from websites using advanced parsing techniques</li>
        <li><strong>AI-Powered Email Generation:</strong> Create personalized cold emails using Google's Gemini AI</li>
        <li><strong>Automated Email Sending:</strong> Send bulk emails through your preferred SMTP provider</li>
        <li><strong>Comprehensive Tracking:</strong> Monitor email history and campaign performance</li>
        <li><strong>Professional Interface:</strong> Modern, accessible UI with keyboard shortcuts</li>
        <li><strong>Data Security:</strong> Local data storage with encrypted credentials</li>
        </ul>
        
        <h3>Technology Stack</h3>
        <ul>
        <li><strong>Framework:</strong> PyQt6 for the user interface</li>
        <li><strong>Web Scraping:</strong> Playwright and BeautifulSoup4</li>
        <li><strong>AI Integration:</strong> Google Generative AI (Gemini)</li>
        <li><strong>Database:</strong> SQLite for local data storage</li>
        <li><strong>Email:</strong> SMTP protocol for email sending</li>
        <li><strong>Security:</strong> System keyring for credential storage</li>
        </ul>
        
        <h3>System Requirements</h3>
        <ul>
        <li><strong>Operating System:</strong> Windows 10+, macOS 10.14+, or Linux</li>
        <li><strong>Python:</strong> 3.8 or higher</li>
        <li><strong>Memory:</strong> 4GB RAM minimum, 8GB recommended</li>
        <li><strong>Storage:</strong> 500MB free space</li>
        <li><strong>Internet:</strong> Stable internet connection required</li>
        </ul>
        
        <h3>Privacy & Security</h3>
        <p>Your privacy and data security are our top priorities:</p>
        <ul>
        <li>All scraped data is stored locally on your computer</li>
        <li>API keys and passwords are encrypted using system keyring</li>
        <li>No data is transmitted to external servers except for AI API calls and email sending</li>
        <li>You maintain full control over your data at all times</li>
        </ul>
        
        <h3>License & Usage</h3>
        <p>This application is provided as-is for educational and professional use. Please ensure compliance with:</p>
        <ul>
        <li>Website terms of service when scraping</li>
        <li>Email marketing regulations (CAN-SPAM, GDPR, etc.)</li>
        <li>API provider terms of service</li>
        <li>Local laws and regulations</li>
        </ul>
        
        <div style="background-color: #F5F5F5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
        <h4>Support & Feedback</h4>
        <p>For support, feature requests, or bug reports, please refer to the application documentation or contact your system administrator.</p>
        <p><strong>Version:</strong> 1.0.0<br>
        <strong>Build Date:</strong> 2024<br>
        <strong>© 2024 Web Scraper Email Automation Tool</strong></p>
        </div>
        """)
        
        layout.addWidget(text)
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "ℹ️ About")


def show_help_dialog(parent=None):
    """
    Show the comprehensive help dialog
    
    Args:
        parent: Parent widget for the dialog
    """
    dialog = HelpDialog(parent)
    dialog.exec()


def show_quick_help(parent=None):
    """
    Show a quick help tooltip or popup
    
    Args:
        parent: Parent widget for the help
    """
    from PyQt6.QtWidgets import QMessageBox
    
    quick_help_text = """
    <h3>Quick Help</h3>
    
    <p><strong>Getting Started:</strong></p>
    <ol>
    <li>Configure API keys in Settings (Ctrl+4)</li>
    <li>Add URLs in Dashboard (Ctrl+1)</li>
    <li>Generate emails in Email tab (Ctrl+2)</li>
    <li>Track history in History tab (Ctrl+3)</li>
    </ol>
    
    <p><strong>Quick Actions:</strong></p>
    <ul>
    <li>Ctrl+R - Start scraping</li>
    <li>Ctrl+G - Generate emails</li>
    <li>Ctrl+T - Test connections</li>
    <li>Ctrl+/ - Show all shortcuts</li>
    </ul>
    
    <p>Press <strong>F1</strong> for detailed help.</p>
    """
    
    QMessageBox.information(parent, "Quick Help", quick_help_text)