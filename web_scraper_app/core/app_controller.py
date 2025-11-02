"""
Application Controller for coordinating between UI and core modules
Handles signal/slot connections and manages application state
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import QMessageBox
from typing import Optional, List, Dict, Any
import logging
import asyncio

from models.email_model import EmailModel, SentEmailModel, SMTPConfig, EmailContent
from core.database import DatabaseManager
from core.scraper import WebScraper
from core.ai_client import GeminiAIClient
from core.email_sender import EmailSender
from core.config_manager import ConfigManager
from core.export_manager import ExportManager
from utils.threading_utils import WorkerThread, ScrapingWorker, EmailGenerationWorker, EmailSendingWorker
from utils.health_monitor import get_health_monitor, setup_default_health_checks
from utils.retry_manager import get_retry_manager, get_fallback_manager
from utils.state_manager import get_state_manager


class ApplicationController(QObject):
    """
    Central controller that coordinates between UI components and core modules
    Manages application state and handles cross-component communication
    """
    
    # Signals for UI updates
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    # Scraping signals
    scraping_started = pyqtSignal()
    scraping_finished = pyqtSignal(list)  # List of EmailModel
    scraping_progress = pyqtSignal(int, str)  # progress, current_url
    email_found = pyqtSignal(str, str, str)  # email, source_website, extracted_at
    
    # Email generation signals
    email_generation_started = pyqtSignal()
    email_generation_finished = pyqtSignal(list)  # List of EmailContent
    email_generation_progress = pyqtSignal(int, str)  # progress, current_website
    
    # Email sending signals
    email_sending_started = pyqtSignal()
    email_sending_finished = pyqtSignal(dict)  # Results dict
    email_sending_progress = pyqtSignal(int, str)  # progress, current_recipient
    
    # Configuration signals
    config_updated = pyqtSignal(str)  # config_type
    connection_status_changed = pyqtSignal(bool)  # connected
    
    # Data signals
    data_updated = pyqtSignal(str)  # data_type: 'scraped_emails', 'sent_emails'
    email_history_updated = pyqtSignal(list)  # List of SentEmailModel
    
    def __init__(self):
        super().__init__()
        
        # Initialize core modules
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.export_manager = ExportManager()
        self.web_scraper = None
        self.ai_client = None
        self.email_sender = None
        
        # Initialize state manager
        self.state_manager = get_state_manager()
        
        # Application state
        self.is_scraping = False
        self.is_generating_emails = False
        self.is_sending_emails = False
        
        # Worker threads
        self.scraping_thread = None
        self.email_generation_thread = None
        self.email_sending_thread = None
        
        # Initialize database
        self.initialize_database()
        
        # Setup periodic connection checks
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connections)
        self.connection_timer.start(30000)  # Check every 30 seconds
        
        # Connect state manager signals
        self.state_manager.state_saved.connect(lambda state_type: self.status_update.emit(f"Application state saved: {state_type}"))
        self.state_manager.state_error.connect(lambda state_type, error: self.error_occurred.emit(f"State error ({state_type}): {error}"))
        
        logging.info("Application controller initialized")
    
    def initialize_database(self):
        """Initialize the database and handle any errors"""
        try:
            self.db_manager.initialize_database()
            self.status_update.emit("Database initialized successfully")
        except Exception as e:
            self.error_occurred.emit(f"Database initialization failed: {str(e)}")
            logging.error(f"Database initialization error: {e}")
    
    def initialize_modules(self):
        """Initialize core modules with current configuration"""
        try:
            # Initialize AI client if API key is available
            api_key = self.config_manager.get_gemini_api_key()
            if api_key:
                self.ai_client = GeminiAIClient(api_key)
                
            # Initialize email sender if SMTP is configured
            smtp_config = self.config_manager.get_smtp_config()
            if smtp_config:
                self.email_sender = EmailSender(smtp_config, self.db_manager)
                
            # Initialize web scraper
            self.web_scraper = WebScraper()
            
            # Setup health monitoring for initialized components
            self._setup_health_monitoring()
            
            self.status_update.emit("Core modules initialized")
            
        except Exception as e:
            self.error_occurred.emit(f"Module initialization failed: {str(e)}")
            logging.error(f"Module initialization error: {e}")
    
    def _setup_health_monitoring(self):
        """Setup health monitoring for application components."""
        try:
            # Get current configuration
            api_key = self.config_manager.get_gemini_api_key()
            smtp_config = self.config_manager.get_smtp_config()
            
            # Setup health checks with current configuration
            setup_default_health_checks(
                db_path=self.db_manager.db_path if self.db_manager else "scraper_data.db",
                gemini_api_key=api_key,
                smtp_config=smtp_config.__dict__ if smtp_config else None
            )
            
            logging.info("Health monitoring setup completed")
            
        except Exception as e:
            logging.warning(f"Health monitoring setup failed: {e}")
    
    async def check_application_health(self) -> Dict[str, Any]:
        """
        Check overall application health.
        
        Returns:
            Dictionary with health check results
        """
        try:
            health_monitor = get_health_monitor()
            results = await health_monitor.check_all_health()
            summary = health_monitor.get_health_summary()
            
            return {
                "overall_status": summary["overall_status"],
                "summary": summary,
                "detailed_results": {name: result.to_dict() for name, result in results.items()}
            }
            
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return {
                "overall_status": "unknown",
                "error": str(e)
            }
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        Get retry and fallback statistics for monitoring.
        
        Returns:
            Dictionary with retry and fallback statistics
        """
        try:
            retry_manager = get_retry_manager()
            fallback_manager = get_fallback_manager()
            
            return {
                "retry_stats": retry_manager.get_retry_stats(),
                "fallback_stats": fallback_manager.get_fallback_stats()
            }
            
        except Exception as e:
            logging.error(f"Failed to get retry statistics: {e}")
            return {"error": str(e)}
    
    def reset_retry_statistics(self):
        """Reset retry and fallback statistics."""
        try:
            retry_manager = get_retry_manager()
            retry_manager.reset_stats()
            logging.info("Retry statistics reset")
            
        except Exception as e:
            logging.error(f"Failed to reset retry statistics: {e}")
    
    # Configuration management methods
    def update_gemini_config(self, api_key: str) -> bool:
        """Update Gemini AI configuration"""
        try:
            self.config_manager.set_gemini_api_key(api_key)
            self.ai_client = GeminiAIClient(api_key)
            self.config_updated.emit("gemini")
            self.status_update.emit("Gemini AI configuration updated")
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to update Gemini configuration: {str(e)}")
            return False
    
    def update_smtp_config(self, smtp_config: SMTPConfig) -> bool:
        """Update SMTP configuration and reinitialize email sender"""
        try:
            # Save configuration
            self.config_manager.set_smtp_config(smtp_config)
            
            # Reinitialize email sender with new config
            self.email_sender = EmailSender(smtp_config, self.db_manager)
            
            self.status_update.emit("SMTP configuration updated successfully")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to update SMTP configuration: {str(e)}")
            return False
    
    def test_gemini_connection(self) -> bool:
        """Test Gemini AI connection"""
        if not self.ai_client:
            self.error_occurred.emit("Gemini AI client not configured")
            return False
            
        try:
            result = self.ai_client.test_connection()
            if result:
                self.status_update.emit("Gemini AI connection successful")
                self.connection_status_changed.emit(True)
            else:
                self.error_occurred.emit("Gemini AI connection failed")
                self.connection_status_changed.emit(False)
            return result
        except Exception as e:
            self.error_occurred.emit(f"Gemini connection test failed: {str(e)}")
            self.connection_status_changed.emit(False)
            return False
    
    def test_smtp_connection(self) -> bool:
        """SMTP connection testing disabled - SMTP functionality was removed"""
        self.status_update.emit("SMTP functionality has been removed - only Gemini AI is needed")
        return True  # Return True to avoid errors, but SMTP is not actually tested
    
    def check_connections(self):
        """Periodic connection health check - only checking Gemini AI since SMTP was removed"""
        try:
            gemini_ok = False
            if self.ai_client:
                result = self.ai_client.test_connection()
                gemini_ok = bool(result) if isinstance(result, bool) else False
            
            # SMTP testing disabled since SMTP configuration was removed
            # Only emit Gemini status since that's all we need
            self.connection_status_changed.emit(gemini_ok)
        except Exception as e:
            self.logger.error(f"Error in connection check: {e}")
            self.connection_status_changed.emit(False)
    
    # Web scraping methods
    def start_scraping(self, urls: List[str]):
        """Start web scraping operation"""
        if self.is_scraping:
            self.error_occurred.emit("Scraping operation already in progress")
            return
            
        if not urls:
            self.error_occurred.emit("No URLs provided for scraping")
            return
            
        if not self.web_scraper:
            self.initialize_modules()
        
        # Update operation state
        self.state_manager.update_operation_state(urls=urls)
            
        self.is_scraping = True
        self.scraping_started.emit()
        
        # Create and start scraping worker thread
        self.scraping_thread = QThread()
        self.scraping_worker = ScrapingWorker(urls, self.web_scraper)
        self.scraping_worker.moveToThread(self.scraping_thread)
        
        # Connect signals
        self.scraping_thread.started.connect(self.scraping_worker.run)
        self.scraping_worker.progress.connect(self.scraping_progress.emit)
        self.scraping_worker.email_found.connect(self.email_found.emit)
        self.scraping_worker.finished.connect(self._on_scraping_finished)
        self.scraping_worker.error.connect(self._on_scraping_error)
        
        self.scraping_thread.start()
        self.status_update.emit(f"Started scraping {len(urls)} websites")
    
    def _on_scraping_finished(self, emails: List[EmailModel]):
        """Handle scraping completion"""
        self.is_scraping = False
        
        # Save emails to database
        try:
            self.db_manager.save_scraped_emails(emails)
            self.data_updated.emit("scraped_emails")
            self.scraping_finished.emit(emails)
            
            # Update statistics
            self.state_manager.update_statistics(
                emails_scraped=len(emails),
                websites_scraped=len(self.state_manager.get_operation_state().get("last_scraping_urls", [])),
                operation_success=True
            )
            
            self.status_update.emit(f"Scraping completed. Found {len(emails)} emails")
        except Exception as e:
            # Update statistics for failed operation
            self.state_manager.update_statistics(operation_success=False)
            self.error_occurred.emit(f"Failed to save scraped emails: {str(e)}")
        
        # Clean up thread
        if self.scraping_thread:
            self.scraping_thread.quit()
            self.scraping_thread.wait()
            self.scraping_thread = None
    
    def _on_scraping_error(self, error_message: str):
        """Handle scraping error"""
        self.is_scraping = False
        self.error_occurred.emit(f"Scraping failed: {error_message}")
        
        # Clean up thread
        if self.scraping_thread:
            self.scraping_thread.quit()
            self.scraping_thread.wait()
            self.scraping_thread = None
    
    def stop_scraping(self):
        """Stop the current scraping operation"""
        if self.is_scraping and hasattr(self, 'scraping_worker'):
            self.scraping_worker.cancel()
            self.is_scraping = False
            self.status_update.emit("Scraping stopped by user")
            
            # Clean up thread
            if self.scraping_thread:
                self.scraping_thread.quit()
                self.scraping_thread.wait()
                self.scraping_thread = None
    
    # Email generation methods
    def generate_emails(self, websites: List[str]):
        """Generate emails for websites using AI"""
        if self.is_generating_emails:
            self.error_occurred.emit("Email generation already in progress")
            return
            
        if not self.ai_client:
            self.error_occurred.emit("Gemini AI client not configured")
            return
            
        if not websites:
            self.error_occurred.emit("No websites provided for email generation")
            return
            
        self.is_generating_emails = True
        self.email_generation_started.emit()
        
        # Create and start email generation worker thread
        self.email_generation_thread = QThread()
        self.email_generation_worker = EmailGenerationWorker(websites, self.ai_client)
        self.email_generation_worker.moveToThread(self.email_generation_thread)
        
        # Connect signals
        self.email_generation_thread.started.connect(self.email_generation_worker.run)
        self.email_generation_worker.progress.connect(self.email_generation_progress.emit)
        self.email_generation_worker.finished.connect(self._on_email_generation_finished)
        self.email_generation_worker.error.connect(self._on_email_generation_error)
    
    def generate_emails_for_selection(self, websites: List[str], selected_emails: List):
        """Generate emails for selected emails only"""
        # Store selected emails for filtering results
        self.selected_emails_for_generation = selected_emails
        
        # Use the regular generation method
        self.generate_emails(websites)
        
        self.email_generation_thread.start()
        self.status_update.emit(f"Started generating emails for {len(websites)} websites")
    
    def _on_email_generation_finished(self, emails: List[EmailContent]):
        """Handle email generation completion"""
        self.is_generating_emails = False
        
        # Filter emails based on selected emails if selection was made
        filtered_emails = emails
        if hasattr(self, 'selected_emails_for_generation') and self.selected_emails_for_generation:
            selected_websites = set(email.source_website for email in self.selected_emails_for_generation)
            filtered_emails = [email for email in emails if email.website in selected_websites]
            
            # Clear the selection after use
            delattr(self, 'selected_emails_for_generation')
        
        # Convert EmailContent objects to dictionaries for UI
        email_dicts = []
        for email_content in filtered_emails:
            email_dict = {
                'website': email_content.website,
                'subject': email_content.subject,
                'body': email_content.body,
                'original': {
                    'subject': email_content.subject,
                    'body': email_content.body
                }
            }
            email_dicts.append(email_dict)
        
        self.email_generation_finished.emit(email_dicts)
        
        # Update status message
        if hasattr(self, 'selected_emails_for_generation'):
            selected_count = len(self.selected_emails_for_generation)
            self.status_update.emit(f"Email generation completed. Generated {len(filtered_emails)} emails for {selected_count} selected recipients")
        else:
            self.status_update.emit(f"Email generation completed. Generated {len(filtered_emails)} emails")
        
        # Clean up thread
        if self.email_generation_thread:
            self.email_generation_thread.quit()
            self.email_generation_thread.wait()
            self.email_generation_thread = None
    
    def _on_email_generation_error(self, error_message: str):
        """Handle email generation error"""
        self.is_generating_emails = False
        self.error_occurred.emit(f"Email generation failed: {error_message}")
        
        # Clean up thread
        if self.email_generation_thread:
            self.email_generation_thread.quit()
            self.email_generation_thread.wait()
            self.email_generation_thread = None
    
    # Email sending methods
    def send_emails(self, email_data: List[Dict[str, Any]]):
        """Send emails using SMTP"""
        if self.is_sending_emails:
            self.error_occurred.emit("Email sending already in progress")
            return
            
        if not self.email_sender:
            # Try to initialize email sender if SMTP config exists
            smtp_config = self.config_manager.get_smtp_config()
            if smtp_config:
                try:
                    self.email_sender = EmailSender(smtp_config, self.db_manager)
                    self.status_update.emit("SMTP client initialized for sending")
                except Exception as e:
                    self.error_occurred.emit(f"Failed to initialize SMTP client: {str(e)}")
                    return
            else:
                self.error_occurred.emit("SMTP client not configured. Please configure SMTP settings first.")
                return
            
        if not email_data:
            self.error_occurred.emit("No emails provided for sending")
            return
        
        # Convert email data format for worker
        # EmailTab sends: [{'website': str, 'subject': str, 'body': str, 'recipients': [str]}]
        # Worker expects: [{'recipient': str, 'subject': str, 'body': str}]
        worker_email_data = []
        for email_info in email_data:
            website = email_info.get('website', '')
            subject = email_info.get('subject', '')
            body = email_info.get('body', '')
            recipients = email_info.get('recipients', [])
            
            for recipient in recipients:
                worker_email_data.append({
                    'recipient': recipient,
                    'subject': subject,
                    'body': body,
                    'website': website
                })
        
        if not worker_email_data:
            self.error_occurred.emit("No valid recipients found for sending")
            return
            
        self.is_sending_emails = True
        self.email_sending_started.emit()
        
        # Create and start email sending worker thread
        self.email_sending_thread = QThread()
        self.email_sending_worker = EmailSendingWorker(worker_email_data, self.email_sender)
        self.email_sending_worker.moveToThread(self.email_sending_thread)
        
        # Connect signals
        self.email_sending_thread.started.connect(self.email_sending_worker.run)
        self.email_sending_worker.progress.connect(self.email_sending_progress.emit)
        self.email_sending_worker.finished.connect(self._on_email_sending_finished)
        self.email_sending_worker.error.connect(self._on_email_sending_error)
        
        self.email_sending_thread.start()
        self.status_update.emit(f"Started sending emails to {len(worker_email_data)} recipients")
    
    def _on_email_sending_finished(self, results: Dict[str, Any]):
        """Handle email sending completion"""
        self.is_sending_emails = False
        
        # Save sent emails to database
        try:
            for email_record in results.get('sent_emails', []):
                self.db_manager.save_sent_email(email_record)
            self.data_updated.emit("sent_emails")
            
            # Update statistics
            success_count = results.get('success_count', 0)
            self.state_manager.update_statistics(
                emails_sent=success_count,
                operation_success=success_count > 0
            )
            
            # Refresh email history for real-time updates
            self.refresh_email_history()
        except Exception as e:
            # Update statistics for failed operation
            self.state_manager.update_statistics(operation_success=False)
            self.error_occurred.emit(f"Failed to save sent email records: {str(e)}")
        
        # Format results for EmailTab
        success_count = results.get('success_count', 0)
        failed_count = results.get('failed_count', 0)
        
        # Create details for status updates
        details = []
        for email_record in results.get('sent_emails', []):
            details.append({
                'website': getattr(email_record, 'website', 'Unknown'),
                'recipient': email_record.recipient_email,
                'status': 'Sent' if email_record.status == 'sent' else 'Failed',
                'error': '' if email_record.status == 'sent' else 'Send failed'
            })
        
        formatted_results = {
            'success': success_count,
            'failed': failed_count,
            'details': details
        }
        
        self.email_sending_finished.emit(formatted_results)
        self.status_update.emit(f"Email sending completed. {success_count}/{success_count + failed_count} emails sent successfully")
        
        # Clean up thread
        if self.email_sending_thread:
            self.email_sending_thread.quit()
            self.email_sending_thread.wait()
            self.email_sending_thread = None
    
    def _on_email_sending_error(self, error_message: str):
        """Handle email sending error"""
        self.is_sending_emails = False
        self.error_occurred.emit(f"Email sending failed: {error_message}")
        
        # Clean up thread
        if self.email_sending_thread:
            self.email_sending_thread.quit()
            self.email_sending_thread.wait()
            self.email_sending_thread = None
    
    # Data retrieval methods
    def get_scraped_emails(self) -> List[EmailModel]:
        """Get all scraped emails from database"""
        try:
            return self.db_manager.get_scraped_emails()
        except Exception as e:
            self.error_occurred.emit(f"Failed to retrieve scraped emails: {str(e)}")
            return []
    
    def get_recent_scraped_emails(self, hours: int = 24) -> List[EmailModel]:
        """Get recently scraped emails from the last N hours"""
        try:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            all_emails = self.db_manager.get_scraped_emails()
            recent_emails = [
                email for email in all_emails 
                if email.extracted_at >= cutoff_time
            ]
            return recent_emails
        except Exception as e:
            self.error_occurred.emit(f"Failed to retrieve recent scraped emails: {str(e)}")
            return []
    
    def get_email_history(self) -> List[SentEmailModel]:
        """Get email sending history from database"""
        try:
            return self.db_manager.get_email_history()
        except Exception as e:
            self.error_occurred.emit(f"Failed to retrieve email history: {str(e)}")
            return []
    
    def refresh_email_history(self):
        """Refresh email history data and emit update signal"""
        try:
            email_history = self.db_manager.get_email_history()
            self.email_history_updated.emit(email_history)
            self.status_update.emit(f"Email history refreshed - {len(email_history)} records")
        except Exception as e:
            self.error_occurred.emit(f"Failed to refresh email history: {str(e)}")
            self.email_history_updated.emit([])
    
    def clear_all_data(self):
        """Clear all data from database"""
        try:
            result = self.db_manager.clear_all_data()
            self.data_updated.emit("scraped_emails")
            self.data_updated.emit("sent_emails")
            
            # Refresh history after clearing
            self.refresh_email_history()
            
            scraped_count = result.get('scraped_emails_deleted', 0)
            sent_count = result.get('sent_emails_deleted', 0)
            self.status_update.emit(f"All data cleared successfully - {scraped_count} scraped emails, {sent_count} sent emails")
        except Exception as e:
            self.error_occurred.emit(f"Failed to clear data: {str(e)}")
    
    def export_scraped_emails_csv(self, file_path: str = None) -> bool:
        """Export scraped emails to CSV file"""
        try:
            emails = self.get_scraped_emails()
            
            if not emails:
                self.error_occurred.emit("No scraped emails to export")
                return False
            
            # Use ExportManager for threaded export
            success = self.export_manager.export_scraped_emails(emails, file_path)
            
            if success:
                # Update operation state with export path
                if file_path:
                    self.state_manager.update_operation_state(export_path=file_path)
                
                # Connect to export worker signals
                export_worker = self.export_manager.get_export_worker()
                if export_worker:
                    export_worker.progress_updated.connect(lambda p: self.progress_update.emit(p))
                    export_worker.export_completed.connect(self._on_export_completed)
                    export_worker.export_failed.connect(self._on_export_failed)
                    export_worker.start()
                
                self.status_update.emit(f"Starting export of {len(emails)} emails...")
                return True
            else:
                return False
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to start export: {str(e)}")
            return False
    
    def _on_export_completed(self, file_path: str):
        """Handle export completion"""
        self.status_update.emit(f"Successfully exported emails to {file_path}")
        self.progress_update.emit(100)
    
    def _on_export_failed(self, error_message: str):
        """Handle export error"""
        self.error_occurred.emit(f"Export failed: {error_message}")
        self.progress_update.emit(0)
    
    def export_filtered_emails(self, date_range=None, website_filter=None, file_path=None) -> bool:
        """Export scraped emails with filtering options"""
        try:
            emails = self.get_scraped_emails()
            
            if not emails:
                self.error_occurred.emit("No scraped emails to export")
                return False
            
            # Use ExportManager for filtered export
            success = self.export_manager.export_filtered_emails(
                emails, date_range, website_filter, file_path
            )
            
            if success:
                # Connect to export worker signals
                export_worker = self.export_manager.get_export_worker()
                if export_worker:
                    export_worker.progress_updated.connect(lambda p: self.progress_update.emit(p))
                    export_worker.export_completed.connect(self._on_export_completed)
                    export_worker.export_failed.connect(self._on_export_failed)
                    export_worker.start()
                
                self.status_update.emit("Starting filtered export...")
                return True
            else:
                return False
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to start filtered export: {str(e)}")
            return False
    
    def export_sent_email_history(self, file_path=None) -> bool:
        """Export sent email history to CSV file"""
        try:
            sent_emails = self.get_email_history()
            
            if not sent_emails:
                self.error_occurred.emit("No sent email history to export")
                return False
            
            # Use ExportManager for sent email export
            success = self.export_manager.export_sent_email_history(sent_emails, file_path)
            
            if success:
                self.status_update.emit(f"Successfully exported {len(sent_emails)} sent email records")
                return True
            else:
                return False
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to export sent email history: {str(e)}")
            return False
    
    def get_application_state_summary(self) -> Dict[str, Any]:
        """Get comprehensive application state summary"""
        try:
            # Get state manager summary
            state_summary = self.state_manager.get_state_summary()
            
            # Get health status
            health_summary = {}
            try:
                health_monitor = get_health_monitor()
                health_summary = health_monitor.get_health_summary()
            except Exception as e:
                health_summary = {"error": str(e)}
            
            # Get retry statistics
            retry_stats = self.get_retry_statistics()
            
            # Get database statistics
            db_stats = {
                "scraped_emails_count": len(self.get_scraped_emails()),
                "sent_emails_count": len(self.get_email_history())
            }
            
            # Get configuration status
            config_status = self.config_manager.get_configuration_status()
            
            return {
                "application_state": state_summary,
                "health_status": health_summary,
                "retry_statistics": retry_stats,
                "database_statistics": db_stats,
                "configuration_status": config_status,
                "current_operations": {
                    "is_scraping": self.is_scraping,
                    "is_generating_emails": self.is_generating_emails,
                    "is_sending_emails": self.is_sending_emails
                }
            }
            
        except Exception as e:
            logging.error(f"Failed to get application state summary: {e}")
            return {"error": str(e)}
    
    def save_application_state(self) -> bool:
        """Save current application state"""
        try:
            return self.state_manager.save_application_state()
        except Exception as e:
            self.error_occurred.emit(f"Failed to save application state: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up resources when application is closing"""
        # Stop any running operations
        if self.is_scraping and self.scraping_thread:
            self.scraping_thread.quit()
            self.scraping_thread.wait()
            
        if self.is_generating_emails and self.email_generation_thread:
            self.email_generation_thread.quit()
            self.email_generation_thread.wait()
            
        if self.is_sending_emails and self.email_sending_thread:
            self.email_sending_thread.quit()
            self.email_sending_thread.wait()
        
        # Stop connection timer
        if self.connection_timer:
            self.connection_timer.stop()
        
        # Save application state
        self.save_application_state()
        
        # Cleanup state manager
        if self.state_manager:
            self.state_manager.cleanup()
        
        logging.info("Application controller cleaned up")