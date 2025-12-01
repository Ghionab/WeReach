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
        
        # Add modern styling for better integration
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {self.colors['primary_bg']};
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {self.colors['primary_bg']};
            }}
        """)
        
        # Create the actual content widget
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)  # Add more spacing for better readability
        
        
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
        
        # Debug logging
        self.logger.info(f"Email tab updated with {len(emails)} scraped emails")
    
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
                
                # Checkbox for selection with enhanced styling
                checkbox = QCheckBox()
                checkbox.setChecked(True)  # Default to selected
                checkbox.stateChanged.connect(self.on_scraped_email_selection_changed)
                
                # Create a container widget to center the checkbox
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                
                # Enhanced checkbox styling with modern gold theme
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        spacing: 8px;
                        color: {self.colors['text_primary']};
                    }}
                    QCheckBox::indicator {{
                        width: 22px;
                        height: 22px;
                        border: 2px solid {self.colors['border_default']};
                        border-radius: 5px;
                        background-color: {self.colors['content_bg']};
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: {self.colors['border_focus']};
                        background-color: {self.colors['hover_bg']};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {self.colors['primary_gold']};
                        border-color: {self.colors['primary_gold']};
                        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
                    }}
                """)
                
                self.scraped_emails_table.setCellWidget(row, 0, checkbox_widget)
                
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
            checkbox_widget = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
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
            checkbox_widget = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
        self.on_scraped_email_selection_changed()
    
    def select_none_scraped_emails(self):
        """Deselect all scraped emails"""
        for row in range(self.scraped_emails_table.rowCount()):
            checkbox_widget = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
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
            checkbox_widget = self.scraped_emails_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
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
        
        summary_text = f"Email sending completed:\nSuccessful: {success_count}\nFailed: {failed_count}"
        
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
        # Ensure current and total are integers
        try:
            current = int(current) if not isinstance(current, int) else current
            total = int(total) if not isinstance(total, int) else total
        except (ValueError, TypeError):
            current = 0
            total = 1
            
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
                        status_item.setBackground(QColor(self.colors['success_green']))
                    elif status == 'Failed':
                        from PyQt6.QtGui import QColor
                        status_item.setBackground(QColor(self.colors['danger_red']))
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
            header_item = QListWidgetItem(f"{website} ({len(recipients)} recipients)")
            header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            from PyQt6.QtGui import QColor
            # Get colors from the parent email tab
            colors = get_colors()
            header_item.setBackground(QColor(colors['content_bg']))  # Use modern content background
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