"""
Export manager for handling CSV file generation and data export operations.
"""
import csv
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import QFileDialog, QWidget, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal

from models import EmailModel, SentEmailModel


class ExportException(Exception):
    """Export operation errors."""
    pass


class ExportWorker(QThread):
    """Worker thread for CSV export operations to prevent UI freezing."""
    
    progress_updated = pyqtSignal(int)  # Progress percentage
    export_completed = pyqtSignal(str)  # File path
    export_failed = pyqtSignal(str)     # Error message
    
    def __init__(self, data: List[EmailModel], file_path: str, export_options: Dict[str, Any]):
        super().__init__()
        self.data = data
        self.file_path = file_path
        self.export_options = export_options
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Execute the export operation in a separate thread."""
        try:
            self._export_to_csv()
            self.export_completed.emit(self.file_path)
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            self.export_failed.emit(str(e))
    
    def _export_to_csv(self):
        """Export data to CSV file with progress updates."""
        if not self.data:
            raise ExportException("No data to export")
        
        try:
            with open(self.file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Define CSV headers
                fieldnames = ['email', 'source_website', 'extracted_date', 'extracted_time']
                
                # Add optional fields based on export options
                if self.export_options.get('include_id', False):
                    fieldnames.insert(0, 'id')
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                total_records = len(self.data)
                
                for i, email_model in enumerate(self.data):
                    # Prepare row data
                    row_data = {
                        'email': email_model.email,
                        'source_website': email_model.source_website,
                        'extracted_date': email_model.extracted_at.strftime('%Y-%m-%d'),
                        'extracted_time': email_model.extracted_at.strftime('%H:%M:%S')
                    }
                    
                    # Add optional fields
                    if self.export_options.get('include_id', False) and email_model.id:
                        row_data['id'] = email_model.id
                    
                    writer.writerow(row_data)
                    
                    # Update progress
                    progress = int((i + 1) / total_records * 100)
                    self.progress_updated.emit(progress)
                
                self.logger.info(f"Successfully exported {total_records} records to {self.file_path}")
                
        except IOError as e:
            raise ExportException(f"Failed to write CSV file: {e}")
        except Exception as e:
            raise ExportException(f"Unexpected error during export: {e}")


class ExportManager:
    """Manages CSV export operations for scraped emails and sent email history."""
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        """Initialize export manager with optional parent widget for dialogs."""
        self.parent_widget = parent_widget
        self.logger = logging.getLogger(__name__)
        self.export_worker = None
    
    def get_export_file_path(self, default_filename: str = None) -> Optional[str]:
        """
        Show file save dialog and return selected file path.
        
        Args:
            default_filename: Default filename to suggest
            
        Returns:
            Selected file path or None if cancelled
        """
        try:
            if not default_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"scraped_emails_{timestamp}.csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent_widget,
                "Export Scraped Emails",
                default_filename,
                "CSV Files (*.csv);;All Files (*)"
            )
            
            return file_path if file_path else None
            
        except Exception as e:
            self.logger.error(f"Failed to show file dialog: {e}")
            self._show_error_message("File Dialog Error", f"Failed to open file dialog: {e}")
            return None
    
    def export_scraped_emails(
        self, 
        emails: List[EmailModel], 
        file_path: Optional[str] = None,
        export_options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Export scraped emails to CSV file.
        
        Args:
            emails: List of EmailModel objects to export
            file_path: Target file path (if None, will show file dialog)
            export_options: Dictionary of export options
            
        Returns:
            True if export initiated successfully, False otherwise
        """
        if not emails:
            self._show_error_message("Export Error", "No emails to export.")
            return False
        
        # Get file path if not provided
        if not file_path:
            file_path = self.get_export_file_path()
            if not file_path:
                return False  # User cancelled
        
        # Set default export options
        if export_options is None:
            export_options = {
                'include_id': False,
                'date_format': '%Y-%m-%d',
                'time_format': '%H:%M:%S'
            }
        
        try:
            # Validate file path
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Start export in worker thread
            self.export_worker = ExportWorker(emails, file_path, export_options)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start export: {e}")
            self._show_error_message("Export Error", f"Failed to start export: {e}")
            return False
    
    def export_filtered_emails(
        self,
        emails: List[EmailModel],
        date_range: Optional[tuple] = None,
        website_filter: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> bool:
        """
        Export emails with filtering options.
        
        Args:
            emails: List of EmailModel objects to filter and export
            date_range: Tuple of (start_date, end_date) for filtering
            website_filter: Website URL to filter by
            file_path: Target file path
            
        Returns:
            True if export initiated successfully, False otherwise
        """
        try:
            # Apply filters
            filtered_emails = self._apply_filters(emails, date_range, website_filter)
            
            if not filtered_emails:
                self._show_error_message("Export Error", "No emails match the specified filters.")
                return False
            
            # Generate filename with filter info
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filter_info = []
                
                if date_range:
                    start_str = date_range[0].strftime("%Y%m%d") if date_range[0] else "start"
                    end_str = date_range[1].strftime("%Y%m%d") if date_range[1] else "end"
                    filter_info.append(f"{start_str}_to_{end_str}")
                
                if website_filter:
                    # Clean website name for filename
                    clean_website = "".join(c for c in website_filter if c.isalnum() or c in "._-")[:20]
                    filter_info.append(clean_website)
                
                filter_suffix = "_".join(filter_info)
                default_filename = f"scraped_emails_{timestamp}_{filter_suffix}.csv" if filter_info else f"scraped_emails_{timestamp}.csv"
                
                file_path = self.get_export_file_path(default_filename)
                if not file_path:
                    return False
            
            # Export filtered data
            export_options = {
                'include_id': True,
                'date_format': '%Y-%m-%d',
                'time_format': '%H:%M:%S'
            }
            
            return self.export_scraped_emails(filtered_emails, file_path, export_options)
            
        except Exception as e:
            self.logger.error(f"Failed to export filtered emails: {e}")
            self._show_error_message("Export Error", f"Failed to export filtered emails: {e}")
            return False
    
    def export_sent_email_history(
        self,
        sent_emails: List[SentEmailModel],
        file_path: Optional[str] = None
    ) -> bool:
        """
        Export sent email history to CSV file.
        
        Args:
            sent_emails: List of SentEmailModel objects to export
            file_path: Target file path
            
        Returns:
            True if export initiated successfully, False otherwise
        """
        if not sent_emails:
            self._show_error_message("Export Error", "No sent email history to export.")
            return False
        
        try:
            # Get file path if not provided
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"sent_email_history_{timestamp}.csv"
                file_path = self.get_export_file_path(default_filename)
                if not file_path:
                    return False
            
            # Convert sent emails to CSV format
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'recipient_email', 'subject', 'sent_date', 'sent_time', 'status', 'body_preview']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for sent_email in sent_emails:
                    # Create body preview (first 100 characters)
                    body_preview = sent_email.body[:100] + "..." if len(sent_email.body) > 100 else sent_email.body
                    body_preview = body_preview.replace('\n', ' ').replace('\r', ' ')
                    
                    row_data = {
                        'id': sent_email.id or '',
                        'recipient_email': sent_email.recipient_email,
                        'subject': sent_email.subject,
                        'sent_date': sent_email.sent_at.strftime('%Y-%m-%d'),
                        'sent_time': sent_email.sent_at.strftime('%H:%M:%S'),
                        'status': sent_email.status,
                        'body_preview': body_preview
                    }
                    
                    writer.writerow(row_data)
            
            self.logger.info(f"Successfully exported {len(sent_emails)} sent email records to {file_path}")
            self._show_success_message("Export Successful", f"Sent email history exported to:\n{file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export sent email history: {e}")
            self._show_error_message("Export Error", f"Failed to export sent email history: {e}")
            return False
    
    def _apply_filters(
        self,
        emails: List[EmailModel],
        date_range: Optional[tuple],
        website_filter: Optional[str]
    ) -> List[EmailModel]:
        """Apply filtering criteria to email list."""
        filtered_emails = emails.copy()
        
        # Apply date range filter
        if date_range:
            start_date, end_date = date_range
            if start_date or end_date:
                filtered_emails = [
                    email for email in filtered_emails
                    if self._is_date_in_range(email.extracted_at.date(), start_date, end_date)
                ]
        
        # Apply website filter
        if website_filter:
            website_filter = website_filter.lower().strip()
            filtered_emails = [
                email for email in filtered_emails
                if website_filter in email.source_website.lower()
            ]
        
        return filtered_emails
    
    def _is_date_in_range(self, check_date: date, start_date: Optional[date], end_date: Optional[date]) -> bool:
        """Check if a date falls within the specified range."""
        if start_date and check_date < start_date:
            return False
        if end_date and check_date > end_date:
            return False
        return True
    
    def _show_error_message(self, title: str, message: str):
        """Show error message dialog."""
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, title, message)
        else:
            self.logger.error(f"{title}: {message}")
    
    def _show_success_message(self, title: str, message: str):
        """Show success message dialog."""
        if self.parent_widget:
            QMessageBox.information(self.parent_widget, title, message)
        else:
            self.logger.info(f"{title}: {message}")
    
    def get_export_worker(self) -> Optional[ExportWorker]:
        """Get the current export worker for connecting signals."""
        return self.export_worker
    
    def validate_export_data(self, emails: List[EmailModel]) -> tuple[bool, str]:
        """
        Validate email data before export.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not emails:
            return False, "No emails to export"
        
        # Check for required fields
        for i, email in enumerate(emails):
            if not email.email:
                return False, f"Email address missing at row {i + 1}"
            if not email.source_website:
                return False, f"Source website missing at row {i + 1}"
            if not email.extracted_at:
                return False, f"Extraction date missing at row {i + 1}"
        
        return True, ""
    
    def get_export_summary(self, emails: List[EmailModel]) -> Dict[str, Any]:
        """
        Get summary statistics for export data.
        
        Returns:
            Dictionary with export statistics
        """
        if not emails:
            return {
                'total_emails': 0,
                'unique_websites': 0,
                'date_range': None,
                'websites': []
            }
        
        # Calculate statistics
        total_emails = len(emails)
        websites = list(set(email.source_website for email in emails))
        unique_websites = len(websites)
        
        # Get date range
        dates = [email.extracted_at.date() for email in emails]
        min_date = min(dates)
        max_date = max(dates)
        
        return {
            'total_emails': total_emails,
            'unique_websites': unique_websites,
            'date_range': (min_date, max_date),
            'websites': sorted(websites)
        }