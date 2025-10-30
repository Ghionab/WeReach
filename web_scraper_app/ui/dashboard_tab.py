"""
Dashboard tab for URL input and web scraping operations
"""

import csv
from typing import List, Optional
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, 
    QTableWidgetItem, QProgressBar, QFileDialog, QMessageBox,
    QGroupBox, QSplitter, QHeaderView, QAbstractItemView,
    QFrame, QScrollArea, QDialog, QDateEdit, QComboBox,
    QCheckBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QDate
from PyQt6.QtGui import QFont, QIcon
from utils.validators import URLValidator


class URLListWidget(QTableWidget):
    """Custom table widget for displaying and managing URLs"""
    
    url_removed = pyqtSignal(str)  # Signal when URL is removed
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        
    def setup_table(self):
        """Setup the URL table widget"""
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["URL", "Status", "Actions"])
        
        # Configure table appearance
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Configure selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        
        # Set minimum height
        self.setMinimumHeight(200)
        
    def add_url(self, url: str, status: str = "Ready"):
        """Add a URL to the table"""
        row = self.rowCount()
        self.insertRow(row)
        
        # URL column
        url_item = QTableWidgetItem(url)
        url_item.setFlags(url_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 0, url_item)
        
        # Status column
        status_item = QTableWidgetItem(status)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 1, status_item)
        
        # Actions column - Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setProperty("class", "danger-button")
        remove_btn.clicked.connect(lambda: self.remove_url_row(row))
        self.setCellWidget(row, 2, remove_btn)
        
    def remove_url_row(self, row: int):
        """Remove a URL row from the table"""
        if 0 <= row < self.rowCount():
            url_item = self.item(row, 0)
            if url_item:
                url = url_item.text()
                self.removeRow(row)
                self.url_removed.emit(url)
                
                # Update remove button connections for remaining rows
                self.update_remove_buttons()
    
    def update_remove_buttons(self):
        """Update remove button connections after row removal"""
        for row in range(self.rowCount()):
            remove_btn = self.cellWidget(row, 2)
            if remove_btn:
                # Disconnect old connections and connect new one
                remove_btn.clicked.disconnect()
                remove_btn.clicked.connect(lambda checked, r=row: self.remove_url_row(r))
    
    def get_all_urls(self) -> List[str]:
        """Get all URLs from the table"""
        urls = []
        for row in range(self.rowCount()):
            url_item = self.item(row, 0)
            if url_item:
                urls.append(url_item.text())
        return urls
    
    def update_url_status(self, url: str, status: str):
        """Update the status of a specific URL"""
        for row in range(self.rowCount()):
            url_item = self.item(row, 0)
            if url_item and url_item.text() == url:
                status_item = self.item(row, 1)
                if status_item:
                    status_item.setText(status)
                break
    
    def clear_all_urls(self):
        """Clear all URLs from the table"""
        self.setRowCount(0)


class ScrapingResultsWidget(QTableWidget):
    """Widget for displaying scraping results in real-time"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        
    def setup_table(self):
        """Setup the results table widget with email editing capability"""
        self.setColumnCount(4)  # Added Actions column
        self.setHorizontalHeaderLabels(["Email", "Source Website", "Extracted At", "Actions"])
        
        # Configure table appearance
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Configure selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        
        # Set minimum height
        self.setMinimumHeight(250)
        
        # Connect item changed signal for email editing
        self.itemChanged.connect(self.on_email_edited)
        
    def add_email_result(self, email: str, source_website: str, extracted_at: str):
        """Add an email result to the table with editing capability"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Email column - EDITABLE for manual correction
        email_item = QTableWidgetItem(email)
        email_item.setFlags(email_item.flags() | Qt.ItemFlag.ItemIsEditable)
        email_item.setToolTip("Double-click to edit this email address")
        # Store original email for comparison
        email_item.setData(Qt.ItemDataRole.UserRole, email)
        self.setItem(row, 0, email_item)
        
        # Source website column
        source_item = QTableWidgetItem(source_website)
        source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 1, source_item)
        
        # Extracted at column
        time_item = QTableWidgetItem(extracted_at)
        time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 2, time_item)
        
        # Actions column - Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setProperty("class", "secondary-button")
        reset_btn.setToolTip("Reset email to original extracted value")
        reset_btn.clicked.connect(lambda: self.reset_email(row))
        self.setCellWidget(row, 3, reset_btn)
        
        # Scroll to the new item
        self.scrollToItem(email_item)
    
    def on_email_edited(self, item):
        """Handle email editing"""
        if item.column() == 0:  # Email column
            new_email = item.text().strip()
            original_email = item.data(Qt.ItemDataRole.UserRole)
            
            # Validate the new email
            if self.is_valid_email(new_email):
                # Email is valid, update styling to show it's been edited
                if new_email != original_email:
                    item.setBackground(Qt.GlobalColor.lightGray)
                    item.setToolTip(f"Edited from: {original_email}\nDouble-click to edit further")
                else:
                    item.setBackground(Qt.GlobalColor.white)
                    item.setToolTip("Double-click to edit this email address")
            else:
                # Invalid email, revert to original
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Invalid Email", 
                                  f"'{new_email}' is not a valid email address.\nReverting to original.")
                item.setText(original_email)
    
    def reset_email(self, row):
        """Reset email to original value"""
        email_item = self.item(row, 0)
        if email_item:
            original_email = email_item.data(Qt.ItemDataRole.UserRole)
            email_item.setText(original_email)
            email_item.setBackground(Qt.GlobalColor.white)
            email_item.setToolTip("Double-click to edit this email address")
    
    def is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def get_all_emails(self) -> List[tuple]:
        """Get all emails with their metadata"""
        emails = []
        for row in range(self.rowCount()):
            email_item = self.item(row, 0)
            website_item = self.item(row, 1)
            time_item = self.item(row, 2)
            
            if email_item and website_item and time_item:
                emails.append((
                    email_item.text(),
                    website_item.text(),
                    time_item.text()
                ))
        return emails
    
    def clear_results(self):
        """Clear all results from the table"""
        self.setRowCount(0)
    
    def get_results_count(self) -> int:
        """Get the number of results"""
        return self.rowCount()


class DashboardTab(QWidget):
    """Dashboard tab for URL input and scraping operations"""
    
    # Signals for communication with main window and controller
    start_scraping_requested = pyqtSignal(list)  # List of URLs to scrape
    export_results_requested = pyqtSignal(str)   # File path for export
    export_filtered_requested = pyqtSignal(dict) # Filter options for export
    
    def __init__(self):
        super().__init__()
        self.url_validator = URLValidator()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the dashboard UI with proper scrolling"""
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
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Dashboard - Web Scraping Operations")
        title_label.setProperty("class", "title")
        content_layout.addWidget(title_label)
        
        # Remove decorative help section as requested
        
        # URL Input Section
        url_section = self.create_url_input_section()
        content_layout.addWidget(url_section)
        
        # Scraping Control Section
        control_section = self.create_scraping_control_section()
        content_layout.addWidget(control_section)
        
        # Results Section
        results_section = self.create_results_section()
        content_layout.addWidget(results_section)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
    # Removed decorative help section as requested
    
    def create_url_input_section(self) -> QWidget:
        """Create the URL input and management section"""
        group_box = QGroupBox("URL Input & Management")
        layout = QVBoxLayout(group_box)
        
        # Dynamic URL input - grows as URLs are added
        input_layout = QVBoxLayout()
        
        # URL input label
        input_label = QLabel("Enter URLs (one per line or separated by commas):")
        input_label.setStyleSheet("font-weight: 500; margin-bottom: 5px;")
        input_layout.addWidget(input_label)
        
        # Dynamic text area for URLs
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText(
            "Enter website URLs here:\n"
            "• One URL per line, or separate multiple URLs with commas\n"
            "• Press Ctrl+Enter to add all URLs to the list\n"
            "• Examples:\n"
            "  https://example.com\n"
            "  https://company.com, https://business.org"
        )
        self.url_input.setToolTip(
            "Enter website URLs to scrape for email addresses.\n"
            "• One URL per line or comma-separated\n"
            "• Press Ctrl+Enter to add all URLs to list\n"
            "• Use Ctrl+N to focus this field from anywhere\n"
            "• Supports http:// and https:// URLs\n"
            "• Text area will grow as you add more URLs"
        )
        self.url_input.setAccessibleName("Website URLs Input")
        self.url_input.setAccessibleDescription("Enter website URLs to scrape for email addresses")
        
        # Set initial height and make it dynamic
        self.url_input.setMinimumHeight(80)
        self.url_input.setMaximumHeight(200)
        
        # Connect text changed signal to auto-resize
        self.url_input.textChanged.connect(self.adjust_url_input_height)
        
        input_layout.addWidget(self.url_input)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.add_url_btn = QPushButton("Add URLs to List")
        self.add_url_btn.setProperty("class", "primary-button")
        self.add_url_btn.setToolTip(
            "Add all URLs from the input area to the scraping list\n"
            "Shortcut: Ctrl+Enter in the URL field"
        )
        self.add_url_btn.setAccessibleName("Add URLs Button")
        self.add_url_btn.setAccessibleDescription("Add all entered URLs to the scraping list")
        self.add_url_btn.clicked.connect(self.add_urls_from_input)
        button_layout.addWidget(self.add_url_btn)
        
        # Add keyboard shortcut for Ctrl+Enter
        from PyQt6.QtGui import QShortcut, QKeySequence
        add_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.url_input)
        add_shortcut.activated.connect(self.add_urls_from_input)
        
        button_layout.addStretch()
        input_layout.addLayout(button_layout)
        
        layout.addLayout(input_layout)
        
        # CSV upload section
        csv_layout = QHBoxLayout()
        
        self.upload_csv_btn = QPushButton("Upload CSV File")
        self.upload_csv_btn.setProperty("class", "secondary-button")
        self.upload_csv_btn.setToolTip("Upload a CSV file containing URLs to scrape (one URL per row)")
        self.upload_csv_btn.clicked.connect(self.upload_csv_file)
        csv_layout.addWidget(self.upload_csv_btn)
        
        self.clear_urls_btn = QPushButton("Clear All URLs")
        self.clear_urls_btn.setProperty("class", "danger-button")
        self.clear_urls_btn.setToolTip("Remove all URLs from the scraping list")
        self.clear_urls_btn.clicked.connect(self.clear_all_urls)
        csv_layout.addWidget(self.clear_urls_btn)
        
        csv_layout.addStretch()
        layout.addLayout(csv_layout)
        
        # URL list table
        self.url_list_widget = URLListWidget()
        layout.addWidget(self.url_list_widget)
        
        # URL count label
        self.url_count_label = QLabel("URLs: 0")
        self.url_count_label.setProperty("class", "info-label")
        layout.addWidget(self.url_count_label)
        
        return group_box
    
    def create_scraping_control_section(self) -> QWidget:
        """Create the scraping control section"""
        group_box = QGroupBox("Scraping Controls")
        layout = QVBoxLayout(group_box)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_scraping_btn = QPushButton("Start Scraping")
        self.start_scraping_btn.setProperty("class", "primary-button")
        self.start_scraping_btn.setToolTip(
            "Begin scraping all URLs in the list for email addresses\n"
            "• Shortcut: Ctrl+R\n"
            "• Requires at least one URL in the list\n"
            "• Shows real-time progress and results"
        )
        self.start_scraping_btn.setAccessibleName("Start Scraping Button")
        self.start_scraping_btn.setAccessibleDescription("Begin scraping all URLs for email addresses")
        self.start_scraping_btn.clicked.connect(self.start_scraping)
        button_layout.addWidget(self.start_scraping_btn)
        
        self.stop_scraping_btn = QPushButton("Stop Scraping")
        self.stop_scraping_btn.setProperty("class", "danger-button")
        self.stop_scraping_btn.setToolTip("Stop the current scraping operation (Esc)")
        self.stop_scraping_btn.setEnabled(False)
        button_layout.addWidget(self.stop_scraping_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to start scraping")
        self.status_label.setProperty("class", "status-label")
        layout.addWidget(self.status_label)
        
        return group_box
    
    def create_results_section(self) -> QWidget:
        """Create the results display section"""
        group_box = QGroupBox("Scraping Results")
        layout = QVBoxLayout(group_box)
        
        # Results table
        self.results_widget = ScrapingResultsWidget()
        layout.addWidget(self.results_widget)
        
        # Results summary and export
        summary_layout = QHBoxLayout()
        
        self.results_count_label = QLabel("Found emails: 0")
        self.results_count_label.setProperty("class", "info-label")
        summary_layout.addWidget(self.results_count_label)
        
        summary_layout.addStretch()
        
        # Export buttons
        self.export_csv_btn = QPushButton("Export All to CSV")
        self.export_csv_btn.setProperty("class", "secondary-button")
        self.export_csv_btn.setToolTip("Export all scraped email addresses to a CSV file (Ctrl+E)")
        self.export_csv_btn.clicked.connect(self.export_results)
        self.export_csv_btn.setEnabled(False)
        summary_layout.addWidget(self.export_csv_btn)
        
        self.export_filtered_btn = QPushButton("Export with Filters...")
        self.export_filtered_btn.setProperty("class", "secondary-button")
        self.export_filtered_btn.setToolTip("Export scraped emails with date range and website filters")
        self.export_filtered_btn.clicked.connect(self.export_filtered_results)
        self.export_filtered_btn.setEnabled(False)
        summary_layout.addWidget(self.export_filtered_btn)
        
        self.clear_results_btn = QPushButton("Clear Results")
        self.clear_results_btn.setProperty("class", "danger-button")
        self.clear_results_btn.setToolTip("Clear all scraped email results from the display")
        self.clear_results_btn.clicked.connect(self.clear_results)
        summary_layout.addWidget(self.clear_results_btn)
        
        layout.addLayout(summary_layout)
        
        return group_box
    
    def connect_signals(self):
        """Connect internal signals"""
        self.url_list_widget.url_removed.connect(self.update_url_count)
        
    def adjust_url_input_height(self):
        """Dynamically adjust the height of the URL input based on content"""
        document = self.url_input.document()
        height = document.size().height()
        
        # Add some padding and limit the height
        new_height = min(max(int(height) + 20, 80), 200)
        self.url_input.setFixedHeight(new_height)
    
    def add_urls_from_input(self):
        """Add URLs from the input field (supports multiple URLs)"""
        text = self.url_input.toPlainText().strip()
        
        if not text:
            return
        
        # Parse URLs - support both line-separated and comma-separated
        urls = []
        
        # First split by lines
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # Then split by commas
                comma_separated = [url.strip() for url in line.split(',')]
                urls.extend(comma_separated)
        
        # Remove empty strings
        urls = [url for url in urls if url]
        
        if not urls:
            return
        
        # Validate and add URLs
        added_count = 0
        skipped_count = 0
        invalid_count = 0
        existing_urls = self.url_list_widget.get_all_urls()
        
        for url in urls:
            # Validate URL
            validation_result = self.url_validator.validate(url)
            
            if not validation_result.is_valid:
                invalid_count += 1
                continue
                
            # Check for duplicates
            if url in existing_urls:
                skipped_count += 1
                continue
                
            # Add URL to list
            self.url_list_widget.add_url(url)
            existing_urls.append(url)
            added_count += 1
        
        # Clear input and update UI
        self.url_input.clear()
        self.update_url_count()
        
        # Show summary message
        message_parts = []
        if added_count > 0:
            message_parts.append(f"{added_count} URLs added")
        if skipped_count > 0:
            message_parts.append(f"{skipped_count} duplicates skipped")
        if invalid_count > 0:
            message_parts.append(f"{invalid_count} invalid URLs skipped")
        
        if message_parts:
            summary = ", ".join(message_parts)
            self.status_label.setText(f"URL processing: {summary}")
            
            if invalid_count > 0:
                QMessageBox.warning(
                    self, 
                    "Invalid URLs", 
                    f"Some URLs were invalid and skipped.\n"
                    f"Added: {added_count}, Skipped: {skipped_count}, Invalid: {invalid_count}"
                )
        else:
            self.status_label.setText("No valid URLs to add")
    
    def upload_csv_file(self):
        """Upload and parse CSV file containing URLs"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            urls_added = 0
            urls_skipped = 0
            existing_urls = self.url_list_widget.get_all_urls()
            
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Try to detect if file has headers
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                # Use csv.Sniffer to detect delimiter
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.reader(csvfile, delimiter=delimiter)
                
                # Skip header row if it looks like headers
                first_row = next(reader, None)
                if first_row and not any(self.url_validator.validate_url(cell.strip())[0] for cell in first_row):
                    # First row doesn't contain valid URLs, assume it's a header
                    pass
                else:
                    # First row contains URLs, process it
                    csvfile.seek(0)
                    reader = csv.reader(csvfile, delimiter=delimiter)
                
                for row in reader:
                    for cell in row:
                        url = cell.strip()
                        if url:
                            validation_result = self.url_validator.validate(url)
                            if validation_result.is_valid:
                                if url not in existing_urls:
                                    self.url_list_widget.add_url(url)
                                    existing_urls.append(url)
                                    urls_added += 1
                                else:
                                    urls_skipped += 1
            
            # Update UI
            self.update_url_count()
            
            # Show summary
            message = f"CSV import completed:\n• {urls_added} URLs added\n• {urls_skipped} URLs skipped (duplicates)"
            QMessageBox.information(self, "CSV Import", message)
            
            self.status_label.setText(f"Imported {urls_added} URLs from CSV")
            
        except Exception as e:
            QMessageBox.critical(self, "CSV Import Error", f"Failed to import CSV file:\n{str(e)}")
    
    def clear_all_urls(self):
        """Clear all URLs from the list"""
        if self.url_list_widget.rowCount() == 0:
            return
            
        reply = QMessageBox.question(
            self,
            "Clear URLs",
            "Are you sure you want to clear all URLs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.url_list_widget.clear_all_urls()
            self.update_url_count()
            self.status_label.setText("All URLs cleared")
    
    def update_url_count(self):
        """Update the URL count label"""
        count = self.url_list_widget.rowCount()
        self.url_count_label.setText(f"URLs: {count}")
        
        # Enable/disable start scraping button
        self.start_scraping_btn.setEnabled(count > 0)
    
    def start_scraping(self):
        """Start the scraping process"""
        urls = self.url_list_widget.get_all_urls()
        
        if not urls:
            QMessageBox.warning(self, "No URLs", "Please add some URLs to scrape.")
            return
            
        # Clear previous results
        self.clear_results()
        
        # Update UI state
        self.start_scraping_btn.setEnabled(False)
        self.stop_scraping_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(urls))
        self.progress_bar.setValue(0)
        
        self.status_label.setText(f"Starting to scrape {len(urls)} websites...")
        
        # Emit signal to start scraping
        self.start_scraping_requested.emit(urls)
    
    def stop_scraping(self):
        """Stop the scraping process"""
        # This will be connected to the controller's stop method
        self.start_scraping_btn.setEnabled(True)
        self.stop_scraping_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Scraping stopped by user")
    
    def on_scraping_progress(self, current: int, total: int, current_url: str = ""):
        """Handle scraping progress updates"""
        self.progress_bar.setValue(current)
        
        if current_url:
            self.status_label.setText(f"Scraping {current}/{total}: {current_url}")
            self.url_list_widget.update_url_status(current_url, "Scraping...")
    
    def on_scraping_completed(self):
        """Handle scraping completion"""
        self.start_scraping_btn.setEnabled(True)
        self.stop_scraping_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        results_count = self.results_widget.get_results_count()
        self.status_label.setText(f"Scraping completed! Found {results_count} emails.")
        
        # Enable export buttons if we have results
        self.export_csv_btn.setEnabled(results_count > 0)
        self.export_filtered_btn.setEnabled(results_count > 0)
        
        # Update all URL statuses to "Completed"
        urls = self.url_list_widget.get_all_urls()
        for url in urls:
            self.url_list_widget.update_url_status(url, "Completed")
    
    def on_scraping_error(self, url: str, error_message: str):
        """Handle scraping errors for individual URLs"""
        self.url_list_widget.update_url_status(url, "Error")
        # Could add more detailed error handling here
    
    def on_email_found(self, email: str, source_website: str, extracted_at: str):
        """Handle new email found during scraping"""
        self.results_widget.add_email_result(email, source_website, extracted_at)
        
        # Update results count
        count = self.results_widget.get_results_count()
        self.results_count_label.setText(f"Found emails: {count}")
        
        # Enable export buttons
        self.export_csv_btn.setEnabled(True)
        self.export_filtered_btn.setEnabled(True)
    
    def export_results(self):
        """Export scraping results to CSV"""
        if self.results_widget.get_results_count() == 0:
            QMessageBox.information(self, "No Results", "No results to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scraping Results",
            "scraped_emails.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.export_results_requested.emit(file_path)
    
    def export_filtered_results(self):
        """Export scraping results with filtering options"""
        if self.results_widget.get_results_count() == 0:
            QMessageBox.information(self, "No Results", "No results to export.")
            return
        
        # Show export filter dialog
        dialog = ExportFilterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            filter_options = dialog.get_filter_options()
            
            # Emit signal with filter options
            self.export_filtered_requested.emit(filter_options)
    
    def clear_results(self):
        """Clear all scraping results"""
        self.results_widget.clear_results()
        self.results_count_label.setText("Found emails: 0")
        self.export_csv_btn.setEnabled(False)
        self.export_filtered_btn.setEnabled(False)
        self.status_label.setText("Results cleared")
    
    def on_scraping_started(self):
        """Handle scraping started signal from controller"""
        # Update UI state for scraping
        self.start_scraping_btn.setEnabled(False)
        self.stop_scraping_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Scraping started...")
    
    def on_scraping_finished(self, emails: List):
        """Handle scraping finished signal from controller"""
        # Update UI state
        self.start_scraping_btn.setEnabled(True)
        self.stop_scraping_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # Update results display
        for email in emails:
            self.on_email_found(
                email.email, 
                email.source_website, 
                email.extracted_at.strftime("%Y-%m-%d %H:%M:%S")
            )
        
        results_count = len(emails)
        self.status_label.setText(f"Scraping completed! Found {results_count} emails.")
        
        # Enable export buttons if we have results
        self.export_csv_btn.setEnabled(results_count > 0)
        self.export_filtered_btn.setEnabled(results_count > 0)
        
        # Update all URL statuses to "Completed"
        urls = self.url_list_widget.get_all_urls()
        for url in urls:
            self.url_list_widget.update_url_status(url, "Completed")
    
    def on_scraping_progress(self, progress_percent: int, status_message: str):
        """Handle scraping progress updates from controller"""
        self.progress_bar.setValue(progress_percent)
        self.progress_bar.setMaximum(100)
        
        self.status_label.setText(status_message)
        
        # Extract URL from status message if possible
        if "Scraping:" in status_message:
            current_url = status_message.replace("Scraping:", "").strip()
            self.url_list_widget.update_url_status(current_url, "Scraping...")
    
    def on_scraping_error(self, error_message: str):
        """Handle scraping error from controller"""
        # Update UI state
        self.start_scraping_btn.setEnabled(True)
        self.stop_scraping_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Scraping error: {error_message}")
        
        # Show error message to user
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Scraping Error", f"Scraping failed:\n{error_message}")


class ExportFilterDialog(QDialog):
    """Dialog for configuring export filters"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Filter Options")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Configure Export Filters")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Date range filter
        date_group = QGroupBox("Date Range Filter")
        date_layout = QVBoxLayout(date_group)
        
        self.enable_date_filter = QCheckBox("Filter by date range")
        date_layout.addWidget(self.enable_date_filter)
        
        date_range_layout = QHBoxLayout()
        
        date_range_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))  # Default to 30 days ago
        self.start_date.setCalendarPopup(True)
        self.start_date.setEnabled(False)
        date_range_layout.addWidget(self.start_date)
        
        date_range_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)
        date_range_layout.addWidget(self.end_date)
        
        date_layout.addLayout(date_range_layout)
        layout.addWidget(date_group)
        
        # Website filter
        website_group = QGroupBox("Website Filter")
        website_layout = QVBoxLayout(website_group)
        
        self.enable_website_filter = QCheckBox("Filter by website")
        website_layout.addWidget(self.enable_website_filter)
        
        website_input_layout = QHBoxLayout()
        website_input_layout.addWidget(QLabel("Website contains:"))
        self.website_filter = QLineEdit()
        self.website_filter.setPlaceholderText("Enter website URL or domain")
        self.website_filter.setEnabled(False)
        website_input_layout.addWidget(self.website_filter)
        
        website_layout.addLayout(website_input_layout)
        layout.addWidget(website_group)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_id = QCheckBox("Include record ID in export")
        options_layout.addWidget(self.include_id)
        
        layout.addWidget(options_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        self.enable_date_filter.toggled.connect(self.start_date.setEnabled)
        self.enable_date_filter.toggled.connect(self.end_date.setEnabled)
        self.enable_website_filter.toggled.connect(self.website_filter.setEnabled)
    
    def get_filter_options(self) -> dict:
        """Get the configured filter options"""
        options = {
            'date_range': None,
            'website_filter': None,
            'include_id': self.include_id.isChecked()
        }
        
        # Date range filter
        if self.enable_date_filter.isChecked():
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()
            options['date_range'] = (start_date, end_date)
        
        # Website filter
        if self.enable_website_filter.isChecked():
            website_text = self.website_filter.text().strip()
            if website_text:
                options['website_filter'] = website_text
        
        return options