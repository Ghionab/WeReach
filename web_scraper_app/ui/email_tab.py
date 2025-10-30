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
    send_emails_requested = pyqtSignal(list)  # List of email data dicts
    
    def __init__(self):
        super().__init__()
        self.colors = get_colors()
        self.logger = logging.getLogger(__name__)
        
        # State variables
        self.scraped_emails = []
        self.generated_emails = []
        self.is_generating = False
        self.is_sending = False
        
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
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Generation controls group
        gen_group = QGroupBox("Email Generation")
        gen_layout = QVBoxLayout(gen_group)
        
        # Info label
        info_label = QLabel("Generate AI-powered cold emails for scraped websites")
        info_label.setWordWrap(True)
        gen_layout.addWidget(info_label)
        
        # Generate button
        self.generate_button = QPushButton("Generate Cold Emails")
        self.generate_button.setMinimumHeight(40)
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
        
        # Email list group
        list_group = QGroupBox("Generated Emails")
        list_layout = QVBoxLayout(list_group)
        
        # Email selection table
        self.emails_table = QTableWidget()
        self.emails_table.setColumnCount(4)
        self.emails_table.setHorizontalHeaderLabels([
            "Select", "Website", "Subject", "Status"
        ])
        
        # Configure table with better column sizing
        header = self.emails_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        # Set better column widths for readability
        self.emails_table.setColumnWidth(0, 70)   # Select checkbox
        self.emails_table.setColumnWidth(1, 200)  # Website - wider for better readability
        self.emails_table.setColumnWidth(3, 100)  # Status - slightly wider
        self.emails_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.emails_table.itemSelectionChanged.connect(self.on_email_selected)
        
        # Set minimum height for better readability
        self.emails_table.setMinimumHeight(300)
        
        list_layout.addWidget(self.emails_table)
        
        # Bulk actions
        actions_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_emails)
        actions_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_emails)
        actions_layout.addWidget(select_none_btn)
        
        list_layout.addLayout(actions_layout)
        
        # Sending controls
        send_controls_layout = QVBoxLayout()
        
        # Recipient count label
        self.recipient_count_label = QLabel("0 recipients selected")
        self.recipient_count_label.setProperty("class", "subtitle")
        send_controls_layout.addWidget(self.recipient_count_label)
        
        # Send button
        self.send_button = QPushButton("Send Selected Emails")
        self.send_button.setMinimumHeight(40)
        self.send_button.setToolTip(
            "Send selected emails to scraped recipients\n"
            "• Shortcut: Ctrl+Shift+S\n"
            "• Select emails using checkboxes\n"
            "• Requires SMTP configuration in Settings"
        )
        self.send_button.setAccessibleName("Send Selected Emails Button")
        self.send_button.setAccessibleDescription("Send all selected emails to their respective recipients")
        self.send_button.clicked.connect(self.on_send_emails)
        self.send_button.setEnabled(False)
        send_controls_layout.addWidget(self.send_button)
        
        # Sending progress details
        self.sending_details_label = QLabel("")
        self.sending_details_label.setWordWrap(True)
        send_controls_layout.addWidget(self.sending_details_label)
        
        list_layout.addLayout(send_controls_layout)
        
        left_layout.addWidget(list_group)
        
        return left_widget
    
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
        
        # Get unique websites from scraped emails
        websites = list(set([email.source_website for email in self.scraped_emails]))
        
        if not websites:
            QMessageBox.warning(
                self, 
                "No Websites", 
                "No scraped websites found. Please scrape some websites first in the Dashboard tab."
            )
            return
        
        self.is_generating = True
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText(f"Generating emails for {len(websites)} websites...")
        
        # Emit signal to controller
        self.generate_emails_requested.emit(websites)
    
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
                    # Add recipient emails from scraped data
                    website = email_data['website']
                    recipients = [email.email for email in self.scraped_emails if email.source_website == website]
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
        self.scraped_emails = emails
        self.status_label.setText(f"Ready - {len(emails)} scraped emails available")
    
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
                        status_item.setBackground(self.colors['success_green'])
                    elif status == 'Failed':
                        status_item.setBackground(self.colors['error_red'])
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
            header_item.setBackground(self.parent().colors['light_green'])
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