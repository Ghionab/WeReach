"""
Email Generation and Sending tab for the Web Scraper Email Automation Tool
Handles AI email generation and SMTP email sending functionality
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QTextEdit, QLineEdit,
    QProgressBar, QGroupBox, QSplitter, QCheckBox, QHeaderView,
    QMessageBox, QScrollArea, QFrame, QComboBox, QDialog,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from typing import List, Dict, Optional
import logging

from models.email_model import EmailModel, EmailContent
from ui.styles import get_colors


class EmailTab(QWidget):
    """
    Email Generation and Sending tab widget
    Provides interface for AI email generation and SMTP sending
    """
    
    # Signals for communication with controller
    generate_emails_requested = pyqtSignal(list)  # List of websites
    generate_emails_for_selection_requested = pyqtSignal(list, list)  # websites, selected_emails
    send_emails_requested = pyqtSignal(list)  # List of email data dicts
    
    def __init__(self):
        super().__init__()
        self.colors = get_colors()
        self.logger = logging.getLogger(__name__)
        
        # State variables
        self.scraped_emails = []
        self.selected_scraped_emails = []  # Store selected emails for generation
        self.generated_emails = []
        self.is_generating = False
        self.is_sending = False
        self.session_start_time = None  # Track when the current session started
        
        # UI components will be initialized in setup_ui
        self.generate_button = None
        self.send_button = None
        self.progress_bar = None
        self.status_label = None
        self.emails_table = None
        self.email_preview = None
        self.subject_edit = None
        self.body_edit = None
        self.recipient_count_label = None
        self.sending_details_label = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Initialize the user interface components"""
        # Set the tab content class for styling
        self.setProperty("class", "tab-content")
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel("Email Generation & Sending")
        title_label.setProperty("class", "title")
        main_layout.addWidget(title_label)
        
        # Create main splitter for layout
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Email list and controls
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Email preview and editing
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions - give more space to the left panel (Generated Emails)
        main_splitter.setSizes([600, 500])
        
        # Status and progress section
        status_layout = self.create_status_section()
        main_layout.addLayout(status_layout)
    
    def create_left_panel(self):
        """Create the left panel with email list and generation controls"""
        # Create scroll area for the left panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Add custom styling for better integration
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        
        # Create the actual content widget
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)  # Add more spacing for better readability
        
        # Generation controls group with better spacing
        gen_group = QGroupBox("Email Generation")
        gen_layout = QVBoxLayout(gen_group)
        gen_layout.setSpacing(12)
        
        # Info label with better styling
        info_label = QLabel("Generate AI-powered cold emails for scraped websites")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #555; font-size: 13px; padding: 8px; background-color: #F8F9FA; border-radius: 5px;")
        gen_layout.addWidget(info_label)
        
        # Generate button with better sizing
        self.generate_button = QPushButton("Generate Cold Emails")
        self.generate_button.setMinimumHeight(45)  # Taller for better visibility
        self.generate_button.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.generate_button.setToolTip(
            "Generate AI-powered cold emails for scraped websites\n"
            "• Shortcut: Ctrl+G\n"
            "• Requires scraped websites from Dashboard\n"
            "• Uses Gemini AI to create personalized emails"
        )
        self.generate_button.setAccessibleName("Generate Cold Emails Button")
        self.generate_button.setAccessibleDescription("Generate AI-powered cold emails for all scraped websites")
        self.generate_button.clicked.connect(self.on_generate_emails)
        gen_layout.addWidget(self.generate_button)
        
        left_layout.addWidget(gen_group)
        
        # Current scraped emails section
        scraped_group = QGroupBox("Current Scraped Emails")
        scraped_layout = QVBoxLayout(scraped_group)
        scraped_layout.setSpacing(10)
        
        # Clear data and filter controls
        controls_layout = QHBoxLayout()
        
        # Clear data button
        self.clear_data_btn = QPushButton("Clear All Cached Data")
        self.clear_data_btn.setProperty("class", "danger-button")
        self.clear_data_btn.setToolTip("Clear all cached emails and start fresh")
        self.clear_data_btn.clicked.connect(self.clear_all_cached_data)
        controls_layout.addWidget(self.clear_data_btn)
        
        controls_layout.addStretch()
        
        filter_label = QLabel("Show:")
        controls_layout.addWidget(filter_label)
        
        self.email_filter_combo = QComboBox()
        self.email_filter_combo.addItems([
            "Current session only",
            "Recent (Last 1 hour)", 
            "Recent (Last 24 hours)",
            "All emails"
        ])
        self.email_filter_combo.setCurrentIndex(0)  # Default to current session only
        self.email_filter_combo.currentTextChanged.connect(self.filter_scraped_emails)
        controls_layout.addWidget(self.email_filter_combo)
        
        scraped_layout.addLayout(controls_layout)
        
        # Info about current emails
        self.scraped_info_label = QLabel("No emails scraped yet")
        self.scraped_info_label.setStyleSheet("color: #B0B0B0; font-size: 12px; padding: 5px;")
        scraped_layout.addWidget(self.scraped_info_label)
        
        # Scraped emails table with scroll area
        scraped_scroll = QScrollArea()
        scraped_scroll.setWidgetResizable(True)
        scraped_scroll.setMinimumHeight(200)
        scraped_scroll.setMaximumHeight(300)
        
        self.scraped_emails_table = QTableWidget()
        self.scraped_emails_table.setColumnCount(3)
        self.scraped_emails_table.setHorizontalHeaderLabels(["Select", "Email", "Website"])
        
        # Configure scraped emails table
        scraped_header = self.scraped_emails_table.horizontalHeader()
        scraped_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        scraped_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        scraped_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.scraped_emails_table.setColumnWidth(0, 60)
        self.scraped_emails_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.scraped_emails_table.setAlternatingRowColors(True)
        self.scraped_emails_table.verticalHeader().setDefaultSectionSize(30)
        
        scraped_scroll.setWidget(self.scraped_emails_table)
        scraped_layout.addWidget(scraped_scroll)
        
        # Scraped emails controls
        scraped_controls = QHBoxLayout()
        
        self.select_all_scraped_btn = QPushButton("Select All")
        self.select_all_scraped_btn.clicked.connect(self.select_all_scraped_emails)
        scraped_controls.addWidget(self.select_all_scraped_btn)
        
        self.select_none_scraped_btn = QPushButton("Select None")
        self.select_none_scraped_btn.clicked.connect(self.select_none_scraped_emails)
        scraped_controls.addWidget(self.select_none_scraped_btn)
        
        self.refresh_scraped_btn = QPushButton("Refresh from Dashboard")
        self.refresh_scraped_btn.clicked.connect(self.refresh_scraped_emails)
        scraped_controls.addWidget(self.refresh_scraped_btn)
        
        scraped_controls.addStretch()
        scraped_layout.addLayout(scraped_controls)
        
        left_layout.addWidget(scraped_group)
        
        # Generated emails list group with better spacing
        list_group = QGroupBox("Generated Emails")
        list_layout = QVBoxLayout(list_group)
        list_layout.setSpacing(12)
        
        # Email selection table
        self.emails_table = QTableWidget()
        self.emails_table.setColumnCount(4)
        self.emails_table.setHorizontalHeaderLabels([
            "Select", "Website", "Subject", "Status"
        ])
        
        # Configure table with better column sizing and readability
        header = self.emails_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        # Set better column widths for improved readability
        self.emails_table.setColumnWidth(0, 80)   # Select checkbox - slightly wider
        self.emails_table.setColumnWidth(1, 250)  # Website - much wider for better readability
        self.emails_table.setColumnWidth(3, 120)  # Status - wider for better text display
        
        # Improve table appearance and readability
        self.emails_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.emails_table.setAlternatingRowColors(True)
        self.emails_table.setShowGrid(True)
        self.emails_table.itemSelectionChanged.connect(self.on_email_selected)
        
        # Set better height for readability - allow more rows to be visible
        self.emails_table.setMinimumHeight(350)
        
        # Improve row height for better readability
        self.emails_table.verticalHeader().setDefaultSectionSize(35)
        
        list_layout.addWidget(self.emails_table)
        
        # Bulk actions with better spacing
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.setMinimumHeight(35)  # Make buttons taller for better usability
        select_all_btn.clicked.connect(self.select_all_emails)
        actions_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.setMinimumHeight(35)
        select_none_btn.clicked.connect(self.select_no_emails)
        actions_layout.addWidget(select_none_btn)
        
        # Add stretch to prevent buttons from stretching too wide
        actions_layout.addStretch()
        
        list_layout.addLayout(actions_layout)
        
        # Sending controls with better spacing
        send_controls_layout = QVBoxLayout()
        send_controls_layout.setSpacing(10)
        
        # Add some spacing before sending controls
        list_layout.addSpacing(15)
        
        # Recipient count label with better styling
        self.recipient_count_label = QLabel("0 recipients selected")
        self.recipient_count_label.setProperty("class", "subtitle")
        self.recipient_count_label.setStyleSheet("font-weight: bold; color: #1976D2; padding: 5px;")
        send_controls_layout.addWidget(self.recipient_count_label)
        
        # Send button with better sizing
        self.send_button = QPushButton("Send Selected Emails")
        self.send_button.setMinimumHeight(45)  # Slightly taller for better visibility
        self.send_button.setToolTip(
            "Send selected emails to scraped recipients\n"
            "• Shortcut: Ctrl+Shift+S\n"
            "• Select emails using checkboxes\n"
            "• Note: SMTP functionality has been simplified"
        )
        self.send_button.setAccessibleName("Send Selected Emails Button")
        self.send_button.setAccessibleDescription("Send all selected emails to their respective recipients")
        self.send_button.clicked.connect(self.on_send_emails)
        self.send_button.setEnabled(False)
        send_controls_layout.addWidget(self.send_button)
        
        # Sending progress details with better formatting
        self.sending_details_label = QLabel("")
        self.sending_details_label.setWordWrap(True)
        self.sending_details_label.setStyleSheet("padding: 5px; background-color: #F5F5F5; border-radius: 5px;")
        send_controls_layout.addWidget(self.sending_details_label)
        
        list_layout.addLayout(send_controls_layout)
        
        left_layout.addWidget(list_group)
        
        # Add stretch to push content to top
        left_layout.addStretch()
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(left_widget)
        
        return scroll_area
    
    def create_right_panel(self):
        """Create the right panel with email preview and editing"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Email preview group
        preview_group = QGroupBox("Email Preview & Editing")
        preview_layout = QVBoxLayout(preview_group)
        
        # Subject editing
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Subject:"))
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("Email subject will appear here...")
        self.subject_edit.textChanged.connect(self.on_subject_changed)
        subject_layout.addWidget(self.subject_edit)
        preview_layout.addLayout(subject_layout)
        
        # Body editing
        body_label = QLabel("Body:")
        preview_layout.addWidget(body_label)
        
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Email body will appear here...\n\nYou can edit the content before sending.")
        self.body_edit.textChanged.connect(self.on_body_changed)
        preview_layout.addWidget(self.body_edit)
        
        # Edit controls
        edit_controls = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Original")
        reset_btn.clicked.connect(self.reset_email_content)
        edit_controls.addWidget(reset_btn)
        
        edit_controls.addStretch()
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_email_changes)
        edit_controls.addWidget(save_btn)
        
        preview_layout.addLayout(edit_controls)
        
        right_layout.addWidget(preview_group)
        
        return right_widget
    
    def create_status_section(self):
        """Create the status and progress section"""
        status_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to generate emails")
        status_layout.addWidget(self.status_label)
        
        return status_layout
    
    def setup_connections(self):
        """Setup signal connections"""
        # Additional connections can be added here
        pass
    
    def on_generate_emails(self):
        """Handle generate emails button click"""
        if self.is_generating:
            return
        
        # Get selected scraped emails
        selected_emails = self.get_selected_scraped_emails()
        
        if not selected_emails:
            QMessageBox.warning(
                self, 
                "No Emails Selected", 
                "No emails are selected for generation. Please:\n"
                "1. Make sure you have scraped some websites in the Dashboard tab\n"
                "2. Select the emails you want to generate content for\n"
                "3. Click 'Refresh from Dashboard' if you don't see recent emails"
            )
            return
        
        # Get unique websites from selected emails
        websites = list(set([email.source_website for email in selected_emails]))
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Generate Emails",
            f"Generate AI emails for {len(selected_emails)} selected emails from {len(websites)} websites?\n\n"
            f"Selected websites:\n" + "\n".join(f"• {website}" for website in websites[:5]) + 
            (f"\n... and {len(websites) - 5} more" if len(websites) > 5 else ""),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Store selected emails for use during generation
        self.selected_scraped_emails = selected_emails
        
        self.is_generating = True
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText(f"Generating emails for {len(websites)} websites with {len(selected_emails)} recipients...")
        
        # Emit signal with both websites and selected emails
        self.generate_emails_for_selection_requested.emit(websites, selected_emails)
    
    def on_send_emails(self):
        """Handle send emails button click"""
        if self.is_sending:
            return
        
        # Get selected emails
        selected_emails = self.get_selected_emails()
        
        if not selected_emails:
            QMessageBox.warning(
                self,
                "No Emails Selected",
                "Please select at least one email to send."
            )
            return
        
        # Calculate total recipients
        total_recipients = sum(len(email_data['recipients']) for email_data in selected_emails)
        
        if total_recipients == 0:
            QMessageBox.warning(
                self,
                "No Recipients",
                "No email recipients found for selected websites. Please scrape some websites first."
            )
            return
        
        # Show recipient selection dialog
        if not self.show_recipient_selection_dialog(selected_emails, total_recipients):
            return
        
        # Confirm sending
        reply = QMessageBox.question(
            self,
            "Confirm Sending",
            f"Are you sure you want to send emails to {total_recipients} recipients from {len(selected_emails)} websites?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.start_sending_process(selected_emails, total_recipients)
    
    def show_recipient_selection_dialog(self, selected_emails, total_recipients):
        """Show dialog for recipient selection and confirmation"""
        dialog = RecipientSelectionDialog(selected_emails, total_recipients, self)
        result = dialog.exec()
        
        if result == QMessageBox.DialogCode.Accepted:
            # Update selected emails with filtered recipients
            filtered_emails = dialog.get_filtered_emails()
            selected_emails.clear()
            selected_emails.extend(filtered_emails)
            return True
        
        return False
    
    def start_sending_process(self, selected_emails, total_recipients):
        """Start the email sending process"""
        self.is_sending = True
        self.send_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total_recipients)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Preparing to send {total_recipients} emails...")
        self.sending_details_label.setText("Initializing email sending...")
        
        # Emit signal to controller
        self.send_emails_requested.emit(selected_emails)
    
    def on_email_selected(self):
        """Handle email selection in table"""
        current_row = self.emails_table.currentRow()
        if current_row >= 0 and current_row < len(self.generated_emails):
            email_content = self.generated_emails[current_row]
            self.display_email_preview(email_content)
    
    def on_subject_changed(self):
        """Handle subject text changes"""
        current_row = self.emails_table.currentRow()
        if current_row >= 0 and current_row < len(self.generated_emails):
            self.generated_emails[current_row]['subject'] = self.subject_edit.text()
            # Update table display
            self.emails_table.setItem(current_row, 2, QTableWidgetItem(self.subject_edit.text()[:50] + "..."))
    
    def on_body_changed(self):
        """Handle body text changes"""
        current_row = self.emails_table.currentRow()
        if current_row >= 0 and current_row < len(self.generated_emails):
            self.generated_emails[current_row]['body'] = self.body_edit.toPlainText()
    
    def display_email_preview(self, email_content):
        """Display email content in preview panel"""
        self.subject_edit.setText(email_content.get('subject', ''))
        self.body_edit.setPlainText(email_content.get('body', ''))
    
    def reset_email_content(self):
        """Reset email content to original generated version"""
        current_row = self.emails_table.currentRow()
        if current_row >= 0 and current_row < len(self.generated_emails):
            email_content = self.generated_emails[current_row]
            original_content = email_content.get('original', {})
            if original_content:
                email_content['subject'] = original_content['subject']
                email_content['body'] = original_content['body']
                self.display_email_preview(email_content)
                # Update table
                self.emails_table.setItem(current_row, 2, QTableWidgetItem(email_content['subject'][:50] + "..."))
    
    def save_email_changes(self):
        """Save changes to email content"""
        current_row = self.emails_table.currentRow()
        if current_row >= 0:
            self.status_label.setText("Email changes saved")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def select_all_emails(self):
        """Select all emails in the table"""
        for row in range(self.emails_table.rowCount()):
            checkbox = self.emails_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
        self.update_send_button_state()
    
    def select_no_emails(self):
        """Deselect all emails in the table"""
        for row in range(self.emails_table.rowCount()):
            checkbox = self.emails_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
        self.update_send_button_state()
    
    def get_selected_emails(self):
        """Get list of selected emails for sending"""
        selected = []
        for row in range(self.emails_table.rowCount()):
            checkbox = self.emails_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                if row < len(self.generated_emails):
                    email_data = self.generated_emails[row].copy()
                    # Add recipient emails from SELECTED scraped data only
                    website = email_data['website']
                    selected_scraped = self.get_selected_scraped_emails()
                    recipients = [email.email for email in selected_scraped if email.source_website == website]
                    email_data['recipients'] = recipients
                    selected.append(email_data)
        return selected
    
    def update_send_button_state(self):
        """Update send button enabled state based on selections"""
        has_selection = any(
            self.emails_table.cellWidget(row, 0).isChecked() 
            for row in range(self.emails_table.rowCount())
            if self.emails_table.cellWidget(row, 0)
        )
        
        # Count total recipients for selected emails
        total_recipients = 0
        if has_selection:
            selected_emails = self.get_selected_emails()
            total_recipients = sum(len(email_data['recipients']) for email_data in selected_emails)
        
        # Update recipient count label
        self.recipient_count_label.setText(f"{total_recipients} recipients selected")
        
        # Update send button
        self.send_button.setEnabled(has_selection and not self.is_sending and total_recipients > 0)
        
        if has_selection and total_recipients > 0:
            self.send_button.setText(f"Send to {total_recipients} Recipients")
        else:
            self.send_button.setText("Send Selected Emails")
    
    def update_scraped_emails(self, emails: List[EmailModel]):
        """Update the list of scraped emails"""
        # Set session start time if this is the first update
        if self.session_start_time is None:
            from datetime import datetime
            self.session_start_time = datetime.now()
        
        self.scraped_emails = emails
        self.populate_scraped_emails_table()
        self.status_label.setText(f"Ready - {len(emails)} scraped emails available")
    
    def filter_scraped_emails(self):
        """Filter scraped emails based on selected filter"""
        self.populate_scraped_emails_table()
    
    def populate_scraped_emails_table(self):
        """Populate the scraped emails table with filtering"""
        self.scraped_emails_table.setRowCount(0)
        
        if not self.scraped_emails:
            self.scraped_info_label.setText("No emails scraped yet. Go to Dashboard tab to scrape websites.")
            return
        
        # Apply filter
        filtered_emails = self.apply_email_filter(self.scraped_emails)
        
        if not filtered_emails:
            filter_text = self.email_filter_combo.currentText()
            self.scraped_info_label.setText(f"No emails match the current filter: {filter_text}")
            return
        
        # Group emails by website for better organization
        websites = {}
        for email in filtered_emails:
            website = email.source_website
            if website not in websites:
                websites[website] = []
            websites[website].append(email.email)
        
        filter_text = self.email_filter_combo.currentText()
        
        # Populate table
        row = 0
        for website, emails in websites.items():
            for email_addr in emails:
                self.scraped_emails_table.insertRow(row)
                
                # Checkbox for selection
                checkbox = QCheckBox()
                checkbox.setChecked(True)  # Default to selected
                checkbox.stateChanged.connect(self.on_scraped_email_selection_changed)
                self.scraped_emails_table.setCellWidget(row, 0, checkbox)
                
                # Email address
                email_item = QTableWidgetItem(email_addr)
                email_item.setFlags(email_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.scraped_emails_table.setItem(row, 1, email_item)
                
                # Website
                website_item = QTableWidgetItem(website)
                website_item.setFlags(website_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.scraped_emails_table.setItem(row, 2, website_item)
                
                row += 1
        
        # Update selection info
        self.on_scraped_email_selection_changed()
    
    def apply_email_filter(self, emails):
        """Apply the selected filter to the email list"""
        filter_text = self.email_filter_combo.currentText()
        
        if filter_text == "All emails":
            return emails
        elif filter_text == "Current session only":
            # Only show emails from the current application session
            if self.session_start_time is None:
                return []
            return [email for email in emails if email.extracted_at >= self.session_start_time]
        elif filter_text == "Recent (Last 1 hour)":
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=1)
            return [email for email in emails if email.extracted_at >= cutoff_time]
        elif filter_text == "Recent (Last 24 hours)":
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=24)
            return [email for email in emails if email.extracted_at >= cutoff_time]
        else:
            return emails
    
    def on_scraped_email_selection_changed(self):
        """Handle changes in scraped email selection"""
        selected_count = 0
        for row in range(self.scraped_emails_table.rowCount()):
            checkbox = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        # Update info label
        total_count = self.scraped_emails_table.rowCount()
        filter_text = self.email_filter_combo.currentText()
        self.scraped_info_label.setText(
            f"Showing {total_count} emails ({filter_text}) - {selected_count} selected"
        )
        
        # Enable/disable generate button based on selection
        self.generate_button.setEnabled(selected_count > 0)
    
    def select_all_scraped_emails(self):
        """Select all scraped emails"""
        for row in range(self.scraped_emails_table.rowCount()):
            checkbox = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
        self.on_scraped_email_selection_changed()
    
    def select_none_scraped_emails(self):
        """Deselect all scraped emails"""
        for row in range(self.scraped_emails_table.rowCount()):
            checkbox = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
        self.on_scraped_email_selection_changed()
    
    def clear_all_cached_data(self):
        """Clear all cached email data and start fresh"""
        reply = QMessageBox.question(
            self,
            "Clear All Data",
            "Are you sure you want to clear ALL cached email data?\n\n"
            "This will remove:\n"
            "• All scraped emails\n"
            "• All sent email history\n"
            "• All generated emails\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear database using controller
                main_window = self.window()
                if hasattr(main_window, 'controller'):
                    main_window.controller.clear_all_data()
                
                # Clear UI state
                self.scraped_emails = []
                self.selected_scraped_emails = []
                self.generated_emails = []
                self.session_start_time = None
                
                # Clear tables
                self.scraped_emails_table.setRowCount(0)
                self.emails_table.setRowCount(0)
                
                # Clear preview
                self.subject_edit.clear()
                self.body_edit.clear()
                
                # Update labels
                self.scraped_info_label.setText("All data cleared. Ready for fresh scraping.")
                self.recipient_count_label.setText("0 recipients selected")
                self.status_label.setText("All cached data cleared successfully")
                
                # Update button states
                self.send_button.setEnabled(False)
                self.generate_button.setEnabled(False)  # Disabled until emails are selected
                
                QMessageBox.information(self, "Success", "All cached data cleared successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear data: {str(e)}")
    
    def refresh_scraped_emails(self):
        """Refresh scraped emails from the controller"""
        # Get fresh data from the main window's controller
        main_window = self.window()
        if hasattr(main_window, 'controller'):
            fresh_emails = main_window.controller.get_scraped_emails()
            self.update_scraped_emails(fresh_emails)
        else:
            QMessageBox.information(
                self,
                "Refresh",
                "Unable to refresh emails. Please try restarting the application."
            )
    
    def get_selected_scraped_emails(self):
        """Get only the selected scraped emails for generation"""
        selected_emails = []
        
        # Get currently filtered emails first
        filtered_emails = self.apply_email_filter(self.scraped_emails)
        
        for row in range(self.scraped_emails_table.rowCount()):
            checkbox = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                email_item = self.scraped_emails_table.item(row, 1)
                website_item = self.scraped_emails_table.item(row, 2)
                
                if email_item and website_item:
                    # Find the corresponding EmailModel from filtered emails
                    email_addr = email_item.text()
                    website = website_item.text()
                    
                    for email_model in filtered_emails:
                        if email_model.email == email_addr and email_model.source_website == website:
                            selected_emails.append(email_model)
                            break
        
        return selected_emails
    
    def on_emails_generated(self, generated_emails: List[Dict]):
        """Handle successful email generation"""
        self.generated_emails = generated_emails
        self.populate_emails_table()
        
        self.is_generating = False
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Generated {len(generated_emails)} emails successfully")
    
    def on_generation_started(self):
        """Handle email generation start"""
        self.is_generating = True
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Generating emails...")
    
    def on_generation_progress(self, progress: int, current_website: str):
        """Handle email generation progress updates"""
        self.status_label.setText(f"Generating email for: {current_website}")
    
    def on_sending_started(self):
        """Handle email sending start"""
        self.is_sending = True
        self.send_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Preparing to send emails...")
    
    def on_generation_error(self, error_message: str):
        """Handle email generation error"""
        if not self.is_generating:
            return  # Error not related to generation
            
        self.is_generating = False
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Email generation failed")
        
        QMessageBox.critical(
            self,
            "Generation Error",
            f"Failed to generate emails:\n{error_message}"
        )
    
    def on_emails_sent(self, results: Dict):
        """Handle email sending completion"""
        self.is_sending = False
        self.send_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        success_count = results.get('success', 0)
        failed_count = results.get('failed', 0)
        
        self.status_label.setText(f"Sent {success_count} emails, {failed_count} failed")
        self.sending_details_label.setText("Sending completed")
        
        # Update table status
        self.update_email_status(results.get('details', []))
        
        # Update send button state
        self.update_send_button_state()
        
        # Show detailed summary
        details = results.get('details', [])
        failed_details = [d for d in details if d.get('status') == 'Failed']
        
        summary_text = f"Email sending completed:\n✓ Successful: {success_count}\n✗ Failed: {failed_count}"
        
        if failed_details:
            summary_text += "\n\nFailed emails:"
            for detail in failed_details[:5]:  # Show first 5 failures
                summary_text += f"\n• {detail.get('recipient', 'Unknown')}: {detail.get('error', 'Unknown error')}"
            if len(failed_details) > 5:
                summary_text += f"\n... and {len(failed_details) - 5} more"
        
        QMessageBox.information(
            self,
            "Sending Complete",
            summary_text
        )
    
    def on_sending_progress(self, current: int, total: int, current_recipient: str = ""):
        """Handle sending progress updates"""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Sending emails... {current}/{total}")
        
        if current_recipient:
            self.sending_details_label.setText(f"Currently sending to: {current_recipient}")
        else:
            percentage = (current / total * 100) if total > 0 else 0
            self.sending_details_label.setText(f"Progress: {percentage:.1f}% complete")
    
    def on_sending_error(self, error_message: str):
        """Handle email sending error"""
        self.is_sending = False
        self.send_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Email sending failed")
        self.sending_details_label.setText("Error occurred during sending")
        
        # Update send button state
        self.update_send_button_state()
        
        QMessageBox.critical(
            self,
            "Sending Error",
            f"Failed to send emails:\n{error_message}"
        )
    
    def populate_emails_table(self):
        """Populate the emails table with generated emails"""
        self.emails_table.setRowCount(len(self.generated_emails))
        
        for row, email_data in enumerate(self.generated_emails):
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.update_send_button_state)
            self.emails_table.setCellWidget(row, 0, checkbox)
            
            # Website
            self.emails_table.setItem(row, 1, QTableWidgetItem(email_data['website']))
            
            # Subject (truncated)
            subject = email_data['subject'][:50] + "..." if len(email_data['subject']) > 50 else email_data['subject']
            self.emails_table.setItem(row, 2, QTableWidgetItem(subject))
            
            # Status
            self.emails_table.setItem(row, 3, QTableWidgetItem("Ready"))
        
        # Select first email by default
        if self.generated_emails:
            self.emails_table.selectRow(0)
            self.display_email_preview(self.generated_emails[0])
    
    def update_email_status(self, status_details: List[Dict]):
        """Update email status in table after sending"""
        for detail in status_details:
            website = detail.get('website')
            status = detail.get('status', 'Unknown')
            
            # Find matching row
            for row in range(self.emails_table.rowCount()):
                if self.emails_table.item(row, 1).text() == website:
                    status_item = QTableWidgetItem(status)
                    if status == 'Sent':
                        from PyQt6.QtGui import QColor
                        status_item.setBackground(QColor('#4CAF50'))  # success_green
                    elif status == 'Failed':
                        from PyQt6.QtGui import QColor
                        status_item.setBackground(QColor('#F44336'))  # error_red
                    self.emails_table.setItem(row, 3, status_item)
                    break


class RecipientSelectionDialog(QDialog):
    """Dialog for selecting specific recipients for email sending"""
    
    def __init__(self, selected_emails, total_recipients, parent=None):
        super().__init__(parent)
        self.selected_emails = selected_emails
        self.total_recipients = total_recipients
        self.filtered_emails = []
        
        self.setWindowTitle("Select Recipients")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
        self.populate_recipients()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"Select recipients from {self.total_recipients} available")
        title.setProperty("class", "subtitle")
        layout.addWidget(title)
        
        # Recipients list
        self.recipients_list = QListWidget()
        layout.addWidget(self.recipients_list)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_recipients)
        controls_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_recipients)
        controls_layout.addWidget(select_none_btn)
        
        controls_layout.addStretch()
        
        # Dialog buttons
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        controls_layout.addWidget(cancel_btn)
        
        send_btn = QPushButton("Send to Selected")
        send_btn.clicked.connect(self.accept)
        controls_layout.addWidget(send_btn)
        
        layout.addLayout(controls_layout)
    
    def populate_recipients(self):
        """Populate the recipients list"""
        for email_data in self.selected_emails:
            website = email_data['website']
            recipients = email_data['recipients']
            
            # Add website header
            header_item = QListWidgetItem(f"📧 {website} ({len(recipients)} recipients)")
            header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            from PyQt6.QtGui import QColor
            header_item.setBackground(QColor('#2D2D2D'))  # Use bg_tertiary color directly
            self.recipients_list.addItem(header_item)
            
            # Add recipients
            for recipient in recipients:
                item = QListWidgetItem(f"   → {recipient}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, {'website': website, 'email': recipient})
                self.recipients_list.addItem(item)
    
    def select_all_recipients(self):
        """Select all recipients"""
        for i in range(self.recipients_list.count()):
            item = self.recipients_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)
    
    def select_no_recipients(self):
        """Deselect all recipients"""
        for i in range(self.recipients_list.count()):
            item = self.recipients_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def get_filtered_emails(self):
        """Get filtered email data with selected recipients only"""
        filtered = []
        
        # Group selected recipients by website
        website_recipients = {}
        for i in range(self.recipients_list.count()):
            item = self.recipients_list.item(i)
            if (item.flags() & Qt.ItemFlag.ItemIsUserCheckable and 
                item.checkState() == Qt.CheckState.Checked):
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    website = data['website']
                    email = data['email']
                    if website not in website_recipients:
                        website_recipients[website] = []
                    website_recipients[website].append(email)
        
        # Create filtered email data
        for email_data in self.selected_emails:
            website = email_data['website']
            if website in website_recipients and website_recipients[website]:
                filtered_data = email_data.copy()
                filtered_data['recipients'] = website_recipients[website]
                filtered.append(filtered_data)
        
        return filtered