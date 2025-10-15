"""
Email management module with threading support for UI integration.
"""
import asyncio
import threading
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging

from models.email_model import SMTPConfig, EmailModel, SentEmailModel, EmailContent
from core.email_sender import EmailSender, SendResult
from core.database import DatabaseManager


class EmailManager:
    """
    High-level email management class that handles threading and UI integration.
    Prevents UI freezing during bulk email operations.
    """
    
    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize EmailManager with database manager.
        
        Args:
            database_manager: Database manager for email operations
        """
        self.database_manager = database_manager
        self.email_sender: Optional[EmailSender] = None
        self.logger = logging.getLogger(__name__)
        
        # Threading control
        self._current_operation_thread: Optional[threading.Thread] = None
        self._stop_operation = threading.Event()
        
        # Callbacks for UI updates
        self.progress_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
    
    def configure_smtp(self, smtp_config: SMTPConfig) -> bool:
        """
        Configure SMTP settings and create email sender.
        
        Args:
            smtp_config: SMTP configuration
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            self.email_sender = EmailSender(
                smtp_config=smtp_config,
                database_manager=self.database_manager,
                progress_callback=self._handle_progress_update
            )
            
            # Test connection
            test_result = self.email_sender.test_smtp_connection()
            
            if test_result['success']:
                self.logger.info("SMTP configuration successful")
                return True
            else:
                self.logger.error(f"SMTP configuration failed: {test_result['message']}")
                if self.error_callback:
                    self.error_callback(f"SMTP test failed: {test_result['message']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to configure SMTP: {e}")
            if self.error_callback:
                self.error_callback(f"SMTP configuration error: {str(e)}")
            return False
    
    def set_callbacks(self, progress_callback: Optional[Callable] = None,
                     completion_callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None):
        """
        Set callback functions for UI updates.
        
        Args:
            progress_callback: Called with (progress_percent, status_message)
            completion_callback: Called with operation result
            error_callback: Called with error message
        """
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
    
    def send_emails_async(self, email_contents: List[Dict[str, str]]) -> bool:
        """
        Start bulk email sending in background thread.
        
        Args:
            email_contents: List of email data dictionaries
            
        Returns:
            True if operation started successfully, False otherwise
        """
        if not self.email_sender:
            if self.error_callback:
                self.error_callback("SMTP not configured. Please configure SMTP settings first.")
            return False
        
        if self._current_operation_thread and self._current_operation_thread.is_alive():
            if self.error_callback:
                self.error_callback("Email sending operation already in progress.")
            return False
        
        # Reset stop event
        self._stop_operation.clear()
        
        # Start email sending in background thread
        self._current_operation_thread = threading.Thread(
            target=self._send_emails_thread,
            args=(email_contents,),
            daemon=True
        )
        self._current_operation_thread.start()
        
        return True
    
    def send_single_email_async(self, recipient: str, subject: str, body: str) -> bool:
        """
        Send single email in background thread.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            
        Returns:
            True if operation started successfully, False otherwise
        """
        if not self.email_sender:
            if self.error_callback:
                self.error_callback("SMTP not configured. Please configure SMTP settings first.")
            return False
        
        if self._current_operation_thread and self._current_operation_thread.is_alive():
            if self.error_callback:
                self.error_callback("Email sending operation already in progress.")
            return False
        
        # Reset stop event
        self._stop_operation.clear()
        
        # Start single email sending in background thread
        self._current_operation_thread = threading.Thread(
            target=self._send_single_email_thread,
            args=(recipient, subject, body),
            daemon=True
        )
        self._current_operation_thread.start()
        
        return True
    
    def stop_operation(self):
        """Stop current email sending operation."""
        self._stop_operation.set()
        self.logger.info("Email sending operation stop requested")
    
    def is_operation_running(self) -> bool:
        """Check if email sending operation is currently running."""
        return (self._current_operation_thread is not None and 
                self._current_operation_thread.is_alive())
    
    def _send_emails_thread(self, email_contents: List[Dict[str, str]]):
        """
        Thread function for bulk email sending.
        
        Args:
            email_contents: List of email data dictionaries
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run bulk email sending
            result = loop.run_until_complete(
                self.email_sender.send_bulk_emails(email_contents)
            )
            
            # Call completion callback with results
            if self.completion_callback and not self._stop_operation.is_set():
                self.completion_callback({
                    'success': True,
                    'result': result,
                    'message': f'Sent {result.successful_sends}/{result.total_emails} emails successfully'
                })
            
        except Exception as e:
            self.logger.error(f"Error in bulk email sending thread: {e}")
            if self.error_callback and not self._stop_operation.is_set():
                self.error_callback(f"Email sending failed: {str(e)}")
        finally:
            # Clean up event loop
            try:
                loop.close()
            except Exception:
                pass
    
    def _send_single_email_thread(self, recipient: str, subject: str, body: str):
        """
        Thread function for single email sending.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Send single email
            result = loop.run_until_complete(
                self.email_sender.send_email(recipient, subject, body)
            )
            
            # Call completion callback with results
            if self.completion_callback and not self._stop_operation.is_set():
                self.completion_callback({
                    'success': result['success'],
                    'result': result,
                    'message': f'Email {"sent successfully" if result["success"] else "failed"} to {recipient}'
                })
            
        except Exception as e:
            self.logger.error(f"Error in single email sending thread: {e}")
            if self.error_callback and not self._stop_operation.is_set():
                self.error_callback(f"Email sending failed: {str(e)}")
        finally:
            # Clean up event loop
            try:
                loop.close()
            except Exception:
                pass
    
    def _handle_progress_update(self, progress: float, message: str):
        """
        Handle progress updates from email sender.
        
        Args:
            progress: Progress percentage (0-100)
            message: Status message
        """
        if self.progress_callback and not self._stop_operation.is_set():
            self.progress_callback(progress, message)
    
    def get_email_history(self, status: Optional[str] = None, limit: Optional[int] = None) -> List[SentEmailModel]:
        """
        Get email sending history.
        
        Args:
            status: Optional status filter
            limit: Optional limit on records
            
        Returns:
            List of sent email records
        """
        return self.database_manager.get_email_history(status=status, limit=limit)
    
    def get_email_statistics(self) -> Dict[str, any]:
        """
        Get email sending statistics.
        
        Returns:
            Dictionary with email statistics
        """
        if self.email_sender:
            return self.email_sender.get_email_statistics()
        else:
            return self.database_manager.get_database_stats()
    
    def retry_failed_emails_async(self, limit: Optional[int] = None) -> bool:
        """
        Retry failed emails in background thread.
        
        Args:
            limit: Optional limit on number of emails to retry
            
        Returns:
            True if operation started successfully, False otherwise
        """
        if not self.email_sender:
            if self.error_callback:
                self.error_callback("SMTP not configured. Please configure SMTP settings first.")
            return False
        
        if self._current_operation_thread and self._current_operation_thread.is_alive():
            if self.error_callback:
                self.error_callback("Email operation already in progress.")
            return False
        
        # Reset stop event
        self._stop_operation.clear()
        
        # Start retry operation in background thread
        self._current_operation_thread = threading.Thread(
            target=self._retry_failed_emails_thread,
            args=(limit,),
            daemon=True
        )
        self._current_operation_thread.start()
        
        return True
    
    def _retry_failed_emails_thread(self, limit: Optional[int] = None):
        """
        Thread function for retrying failed emails.
        
        Args:
            limit: Optional limit on number of emails to retry
        """
        try:
            result = self.email_sender.retry_failed_emails(limit=limit)
            
            # Call completion callback with results
            if self.completion_callback and not self._stop_operation.is_set():
                self.completion_callback({
                    'success': result['success'],
                    'result': result,
                    'message': result['message']
                })
            
        except Exception as e:
            self.logger.error(f"Error in retry failed emails thread: {e}")
            if self.error_callback and not self._stop_operation.is_set():
                self.error_callback(f"Retry operation failed: {str(e)}")
    
    def test_smtp_connection(self) -> Dict[str, any]:
        """
        Test SMTP connection.
        
        Returns:
            Dictionary with test results
        """
        if not self.email_sender:
            return {
                'success': False,
                'message': 'SMTP not configured',
                'details': {}
            }
        
        return self.email_sender.test_smtp_connection()