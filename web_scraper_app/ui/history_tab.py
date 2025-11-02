"""
History tab for displaying sent email tracking and history.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QLineEdit, QPushButton, QComboBox, 
    QTextEdit, QSplitter, QHeaderView, QMessageBox, QGroupBox,
    QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
from typing import List, Optional

from models import SentEmailModel


class HistoryTab(QWidget):
    """Tab widget for displaying email history and tracking."""
    
    # Signals
    refresh_requested = pyqtSignal()
    export_history_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.email_history = []
        self.filtered_history = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the history tab UI components."""
        # Set the tab content class for styling
        self.setProperty("class", "tab-content")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("📋 Email History & Tracking")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Search and filter section
        self.setup_search_section(layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Email history table
        self.setup_history_table(splitter)
        
        # Right side - Email detail view
        self.setup_detail_view(splitter)
        
        # Set splitter proportions (70% table, 30% details)
        splitter.setSizes([700, 300])
        
        # Status section
        self.setup_status_section(layout)
        
    def setup_search_section(self, parent_layout):
        """Setup search and filter controls."""
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout(search_group)
        
        # First row - Search and status filter
        first_row = QHBoxLayout()
        
        # Search input
        search_label = QLabel("Search:")
        first_row.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by recipient email or subject...")
        self.search_input.setToolTip(
            "Search email history by recipient or subject\n"
            "• Type to filter results in real-time\n"
            "• Combine with status filter for better results\n"
            "• Use Ctrl+D to clear search"
        )
        self.search_input.setAccessibleName("Email History Search")
        self.search_input.setAccessibleDescription("Search email history by recipient email or subject")
        first_row.addWidget(self.search_input)
        
        # Status filter
        status_label = QLabel("Status:")
        first_row.addWidget(status_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Sent", "Failed", "Pending"])
        self.status_filter.setMinimumWidth(100)
        first_row.addWidget(self.status_filter)
        
        # Clear filters button
        self.clear_filters_btn = QPushButton("Clear Filters")
        self.clear_filters_btn.setProperty("class", "secondary")
        first_row.addWidget(self.clear_filters_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip(
            "Refresh email history from database\n"
            "Shortcut: F5 (when on History tab)"
        )
        self.refresh_btn.setAccessibleName("Refresh History Button")
        self.refresh_btn.setAccessibleDescription("Refresh email history data from database")
        first_row.addWidget(self.refresh_btn)
        
        # Export button
        self.export_history_btn = QPushButton("📤 Export History")
        self.export_history_btn.setProperty("class", "secondary-button")
        first_row.addWidget(self.export_history_btn)
        
        first_row.addStretch()
        search_layout.addLayout(first_row)
        
        parent_layout.addWidget(search_group)
        
    def setup_history_table(self, parent_splitter):
        """Setup the email history table."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table header
        table_header = QLabel("Sent Email History")
        table_header.setProperty("class", "subtitle")
        table_layout.addWidget(table_header)
        
        # Create table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Recipient", "Subject", "Status", "Sent Date", "ID"
        ])
        
        # Configure table
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setSortingEnabled(True)
        
        # Set default sort by date (descending - newest first)
        self.history_table.sortItems(3, Qt.SortOrder.DescendingOrder)
        
        # Set column widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Recipient
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Subject
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Date
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # ID
        
        self.history_table.setColumnWidth(2, 80)   # Status
        self.history_table.setColumnWidth(3, 150)  # Date
        self.history_table.setColumnWidth(4, 60)   # ID
        
        # Hide ID column by default
        self.history_table.setColumnHidden(4, True)
        
        table_layout.addWidget(self.history_table)
        
        # Table stats
        self.table_stats_label = QLabel("No emails found")
        self.table_stats_label.setStyleSheet("color: #666; font-style: italic;")
        table_layout.addWidget(self.table_stats_label)
        
        parent_splitter.addWidget(table_widget)
        
    def setup_detail_view(self, parent_splitter):
        """Setup the email detail view panel."""
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(10, 0, 0, 0)
        
        # Detail header
        detail_header = QLabel("Email Details")
        detail_header.setProperty("class", "subtitle")
        detail_layout.addWidget(detail_header)
        
        # Email info section
        info_group = QGroupBox("Email Information")
        info_layout = QVBoxLayout(info_group)
        
        # Recipient
        self.detail_recipient = QLabel("Recipient: -")
        self.detail_recipient.setWordWrap(True)
        info_layout.addWidget(self.detail_recipient)
        
        # Subject
        self.detail_subject = QLabel("Subject: -")
        self.detail_subject.setWordWrap(True)
        info_layout.addWidget(self.detail_subject)
        
        # Status
        self.detail_status = QLabel("Status: -")
        info_layout.addWidget(self.detail_status)
        
        # Sent date
        self.detail_sent_date = QLabel("Sent: -")
        info_layout.addWidget(self.detail_sent_date)
        
        detail_layout.addWidget(info_group)
        
        # Email body section
        body_group = QGroupBox("Email Body")
        body_layout = QVBoxLayout(body_group)
        
        self.detail_body = QTextEdit()
        self.detail_body.setReadOnly(True)
        self.detail_body.setMaximumHeight(200)
        body_layout.addWidget(self.detail_body)
        
        detail_layout.addWidget(body_group)
        
        detail_layout.addStretch()
        
        parent_splitter.addWidget(detail_widget)
        
    def setup_status_section(self, parent_layout):
        """Setup status and statistics section."""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        # Statistics labels
        self.total_emails_label = QLabel("Total: 0")
        self.sent_emails_label = QLabel("Sent: 0")
        self.failed_emails_label = QLabel("Failed: 0")
        self.pending_emails_label = QLabel("Pending: 0")
        
        # Style status labels
        for label in [self.total_emails_label, self.sent_emails_label, 
                     self.failed_emails_label, self.pending_emails_label]:
            label.setStyleSheet("font-weight: bold; padding: 5px;")
        
        self.sent_emails_label.setStyleSheet("font-weight: bold; padding: 5px; color: #4CAF50;")
        self.failed_emails_label.setStyleSheet("font-weight: bold; padding: 5px; color: #F44336;")
        self.pending_emails_label.setStyleSheet("font-weight: bold; padding: 5px; color: #FF9800;")
        
        status_layout.addWidget(self.total_emails_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.sent_emails_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.failed_emails_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.pending_emails_label)
        status_layout.addStretch()
        
        # Last updated label
        self.last_updated_label = QLabel("Last updated: Never")
        self.last_updated_label.setStyleSheet("color: #666; font-style: italic;")
        status_layout.addWidget(self.last_updated_label)
        
        parent_layout.addWidget(status_frame)
        
    def setup_connections(self):
        """Setup signal connections."""
        # Search and filter connections
        self.search_input.textChanged.connect(self.apply_filters)
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.export_history_btn.clicked.connect(self.export_history)
        
        # Table selection
        self.history_table.itemSelectionChanged.connect(self.on_selection_changed)
        
    def update_email_history(self, email_history: List[SentEmailModel]):
        """Update the email history data and refresh the display."""
        self.email_history = email_history
        self.apply_filters()
        self.update_statistics()
        self.last_updated_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
    def apply_filters(self):
        """Apply search and status filters to the email history."""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText().lower()
        
        # Filter the email history
        self.filtered_history = []
        for email in self.email_history:
            # Apply search filter
            if search_text:
                if (search_text not in email.recipient_email.lower() and 
                    search_text not in email.subject.lower()):
                    continue
            
            # Apply status filter
            if status_filter != "all" and email.status.lower() != status_filter:
                continue
                
            self.filtered_history.append(email)
        
        # Update table display
        self.populate_table()
        
    def populate_table(self):
        """Populate the history table with filtered data."""
        self.history_table.setRowCount(len(self.filtered_history))
        
        for row, email in enumerate(self.filtered_history):
            # Recipient
            recipient_item = QTableWidgetItem(email.recipient_email)
            self.history_table.setItem(row, 0, recipient_item)
            
            # Subject (truncate if too long)
            subject = email.subject
            if len(subject) > 50:
                subject = subject[:47] + "..."
            subject_item = QTableWidgetItem(subject)
            subject_item.setToolTip(email.subject)  # Full subject in tooltip
            self.history_table.setItem(row, 1, subject_item)
            
            # Status with color coding
            status_item = QTableWidgetItem(email.status.title())
            if email.status == 'sent':
                status_item.setBackground(Qt.GlobalColor.green)
                status_item.setForeground(Qt.GlobalColor.white)
            elif email.status == 'failed':
                status_item.setBackground(Qt.GlobalColor.red)
                status_item.setForeground(Qt.GlobalColor.white)
            elif email.status == 'pending':
                status_item.setBackground(Qt.GlobalColor.yellow)
                status_item.setForeground(Qt.GlobalColor.black)
            self.history_table.setItem(row, 2, status_item)
            
            # Sent date
            date_str = email.sent_at.strftime('%Y-%m-%d %H:%M')
            date_item = QTableWidgetItem(date_str)
            # Set data for proper sorting (use timestamp)
            date_item.setData(Qt.ItemDataRole.UserRole, email.sent_at.timestamp())
            self.history_table.setItem(row, 3, date_item)
            
            # ID (hidden)
            id_item = QTableWidgetItem(str(email.id or ''))
            self.history_table.setItem(row, 4, id_item)
        
        # Update table stats
        total_count = len(self.filtered_history)
        if total_count == 0:
            self.table_stats_label.setText("No emails found")
        elif total_count == len(self.email_history):
            self.table_stats_label.setText(f"Showing all {total_count} emails")
        else:
            self.table_stats_label.setText(f"Showing {total_count} of {len(self.email_history)} emails")
        
        # Clear selection and details
        self.clear_detail_view()
        
    def update_statistics(self):
        """Update the statistics display."""
        total = len(self.email_history)
        sent = sum(1 for email in self.email_history if email.status == 'sent')
        failed = sum(1 for email in self.email_history if email.status == 'failed')
        pending = sum(1 for email in self.email_history if email.status == 'pending')
        
        self.total_emails_label.setText(f"Total: {total}")
        self.sent_emails_label.setText(f"Sent: {sent}")
        self.failed_emails_label.setText(f"Failed: {failed}")
        self.pending_emails_label.setText(f"Pending: {pending}")
        
    def on_selection_changed(self):
        """Handle table selection changes to update detail view."""
        selected_rows = self.history_table.selectionModel().selectedRows()
        
        if not selected_rows:
            self.clear_detail_view()
            return
            
        row = selected_rows[0].row()
        if 0 <= row < len(self.filtered_history):
            email = self.filtered_history[row]
            self.display_email_details(email)
        
    def display_email_details(self, email: SentEmailModel):
        """Display detailed information for the selected email."""
        self.detail_recipient.setText(f"Recipient: {email.recipient_email}")
        self.detail_subject.setText(f"Subject: {email.subject}")
        
        # Status with color
        status_text = f"Status: {email.status.title()}"
        if email.status == 'sent':
            self.detail_status.setText(status_text)
            self.detail_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        elif email.status == 'failed':
            self.detail_status.setText(status_text)
            self.detail_status.setStyleSheet("color: #F44336; font-weight: bold;")
        elif email.status == 'pending':
            self.detail_status.setText(status_text)
            self.detail_status.setStyleSheet("color: #FF9800; font-weight: bold;")
        
        self.detail_sent_date.setText(f"Sent: {email.sent_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.detail_body.setPlainText(email.body)
        
    def clear_detail_view(self):
        """Clear the email detail view."""
        self.detail_recipient.setText("Recipient: -")
        self.detail_subject.setText("Subject: -")
        self.detail_status.setText("Status: -")
        self.detail_status.setStyleSheet("")
        self.detail_sent_date.setText("Sent: -")
        self.detail_body.clear()
        
    def clear_filters(self):
        """Clear all search and filter inputs."""
        self.search_input.clear()
        self.status_filter.setCurrentText("All")
        # Trigger filter update
        self.apply_filters()
        
    def refresh_data(self):
        """Request fresh data from the controller."""
        self.refresh_requested.emit()
    
    def export_history(self):
        """Export email history to CSV."""
        if not self.email_history:
            QMessageBox.information(self, "No Data", "No email history to export.")
            return
        
        self.export_history_requested.emit()
        
    def show_no_data_message(self):
        """Show message when no email history is available."""
        self.history_table.setRowCount(0)
        self.table_stats_label.setText("No email history available")
        self.clear_detail_view()
        self.update_statistics()