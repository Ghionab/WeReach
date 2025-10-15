"""
Email sending module with SMTP integration for the web scraper application.
"""
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor

from models.email_model import SMTPConfig, EmailModel, SentEmailModel, EmailContent
from core.database import DatabaseManager
from utils.retry_manager import (
    RetryConfig, RetryStrategy, async_retry_on_failure,
    with_async_fallback, get_fallback_manager
)
from utils.exceptions import EmailException, RetryableException


@dataclass
class SendResult:
    """Result of bulk email sending operation."""
    total_emails: int
    successful_sends: int
    failed_sends: int
    failed_emails: List[Dict[str, str]]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_emails == 0:
            return 0.0
        return (self.successful_sends / self.total_emails) * 100


class EmailSenderException(Exception):
    """Base exception for email sending operations."""
    pass


class SMTPConnectionException(EmailSenderException):
    """Exception for SMTP connection issues."""
    pass


class EmailSendException(EmailSenderException):
    """Exception for individual email sending failures."""
    pass


class EmailSender:
    """
    Email sender class with SMTP functionality for individual and bulk operations.
    Includes database integration for email history tracking and status management.
    """
    
    def __init__(self, smtp_config: SMTPConfig, database_manager: DatabaseManager, 
                 progress_callback: Optional[Callable] = None):
        """
        Initialize EmailSender with SMTP configuration and database manager.
        
        Args:
            smtp_config: SMTP server configuration
            database_manager: Database manager for email history tracking
            progress_callback: Optional callback for progress updates during bulk sending
        """
        self.smtp_config = smtp_config
        self.database_manager = database_manager
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        # Thread pool for concurrent email sending
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        
        # Register fallback mechanisms
        self._register_fallbacks()
        
        # Common SMTP provider configurations
        self.provider_configs = {
            'gmail': {'server': 'smtp.gmail.com', 'port': 587, 'use_tls': True},
            'outlook': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
            'yahoo': {'server': 'smtp.mail.yahoo.com', 'port': 587, 'use_tls': True},
            'hotmail': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
        }
    
    def _get_provider_config(self, email: str) -> Optional[Dict[str, any]]:
        """
        Get SMTP configuration for common email providers.
        
        Args:
            email: Email address to determine provider
            
        Returns:
            Provider configuration or None if not found
        """
        domain = email.split('@')[1].lower()
        
        if 'gmail' in domain:
            return self.provider_configs['gmail']
        elif 'outlook' in domain or 'hotmail' in domain or 'live' in domain:
            return self.provider_configs['outlook']
        elif 'yahoo' in domain:
            return self.provider_configs['yahoo']
        
        return None
    
    def _register_fallbacks(self):
        """Register fallback mechanisms for email operations."""
        fallback_manager = get_fallback_manager()
        
        # Register fallback for email sending
        fallback_manager.register_fallback(
            "send_email",
            self._fallback_log_email_only,
            priority=1
        )
    
    async def _fallback_log_email_only(self, recipient: str, subject: str, body: str, 
                                     track_in_database: bool = True) -> Dict[str, any]:
        """
        Fallback method that logs email instead of sending when SMTP fails.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            track_in_database: Whether to save email record to database
            
        Returns:
            Dictionary with fallback result
        """
        self.logger.warning(f"Using fallback: logging email to {recipient} instead of sending")
        
        # Create email record with failed status if tracking enabled
        email_record_id = None
        if track_in_database and self.database_manager:
            try:
                email_record = SentEmailModel(
                    recipient_email=recipient,
                    subject=subject,
                    body=body,
                    sent_at=datetime.now(),
                    status="fallback_logged"
                )
                email_record_id = self.database_manager.save_sent_email(email_record)
            except Exception as e:
                self.logger.error(f"Failed to save fallback email record: {e}")
        
        # Log the email content for manual review
        self.logger.info(f"FALLBACK EMAIL - To: {recipient}, Subject: {subject}")
        self.logger.debug(f"FALLBACK EMAIL BODY:\n{body}")
        
        return {
            "success": False,
            "message": "Email logged as fallback (SMTP unavailable)",
            "email_record_id": email_record_id,
            "fallback_used": True
        }
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """
        Create and configure SMTP connection.
        
        Returns:
            Configured SMTP connection
            
        Raises:
            SMTPConnectionException: If connection fails
        """
        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_config.server, self.smtp_config.port)
            
            # Enable debug output for troubleshooting
            server.set_debuglevel(0)
            
            # Start TLS if enabled
            if self.smtp_config.use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            # Login to server
            server.login(self.smtp_config.email, self.smtp_config.password)
            
            self.logger.info(f"Successfully connected to SMTP server: {self.smtp_config.server}")
            return server
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            self.logger.error(error_msg)
            raise SMTPConnectionException(error_msg)
        except smtplib.SMTPConnectError as e:
            error_msg = f"Failed to connect to SMTP server: {str(e)}"
            self.logger.error(error_msg)
            raise SMTPConnectionException(error_msg)
        except Exception as e:
            error_msg = f"Unexpected SMTP connection error: {str(e)}"
            self.logger.error(error_msg)
            raise SMTPConnectionException(error_msg)
    
    def _create_email_message(self, recipient: str, subject: str, body: str) -> MIMEMultipart:
        """
        Create email message with proper headers.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            
        Returns:
            Configured email message
        """
        message = MIMEMultipart()
        message["From"] = self.smtp_config.email
        message["To"] = recipient
        message["Subject"] = subject
        
        # Add body to email
        message.attach(MIMEText(body, "plain"))
        
        return message
    
    @async_retry_on_failure(RetryConfig(
        max_attempts=3,
        base_delay=5.0,
        max_delay=120.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retryable_exceptions=(EmailException, RetryableException, smtplib.SMTPException)
    ))
    @with_async_fallback("send_email")
    async def send_email(self, recipient: str, subject: str, body: str, 
                        track_in_database: bool = True) -> Dict[str, any]:
        """
        Send individual email via SMTP with database tracking.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            track_in_database: Whether to save email record to database
            
        Returns:
            Dictionary with send result and email record ID
            
        Raises:
            EmailSendException: If email sending fails
        """
        email_record_id = None
        
        try:
            # Validate inputs
            if not EmailModel.is_valid_email(recipient):
                raise EmailSendException(f"Invalid recipient email: {recipient}")
            
            if not subject.strip():
                raise EmailSendException("Email subject cannot be empty")
            
            if not body.strip():
                raise EmailSendException("Email body cannot be empty")
            
            # Create email record with pending status if tracking enabled
            if track_in_database:
                email_record = SentEmailModel(
                    recipient_email=recipient,
                    subject=subject,
                    body=body,
                    sent_at=datetime.now(),
                    status='pending'
                )
                email_record_id = self.database_manager.save_sent_email(email_record)
            
            # Run SMTP operations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.thread_pool, 
                self._send_email_sync, 
                recipient, subject, body
            )
            
            # Update status in database
            if track_in_database and email_record_id:
                status = 'sent' if success else 'failed'
                self.database_manager.update_email_status(email_record_id, status)
            
            return {
                'success': success,
                'email_record_id': email_record_id,
                'recipient': recipient,
                'status': 'sent' if success else 'failed'
            }
            
        except EmailSendException:
            # Update status to failed if tracking enabled
            if track_in_database and email_record_id:
                self.database_manager.update_email_status(email_record_id, 'failed')
            raise
        except Exception as e:
            # Update status to failed if tracking enabled
            if track_in_database and email_record_id:
                self.database_manager.update_email_status(email_record_id, 'failed')
            
            error_msg = f"Unexpected error sending email to {recipient}: {str(e)}"
            self.logger.error(error_msg)
            raise EmailSendException(error_msg)
    
    def _send_email_sync(self, recipient: str, subject: str, body: str) -> bool:
        """
        Synchronous email sending method for use in thread pool.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            
        Returns:
            True if email sent successfully, False otherwise
        """
        server = None
        try:
            # Create SMTP connection
            server = self._create_smtp_connection()
            
            # Create email message
            message = self._create_email_message(recipient, subject, body)
            
            # Send email
            text = message.as_string()
            server.sendmail(self.smtp_config.email, recipient, text)
            
            self.logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
    
    async def send_bulk_emails(self, email_contents: List[Dict[str, str]], 
                              max_concurrent: int = 3) -> SendResult:
        """
        Send multiple emails with progress tracking and threading to prevent UI freezing.
        
        Args:
            email_contents: List of dictionaries with 'recipient', 'subject', 'body' keys
            max_concurrent: Maximum number of concurrent email sends
            
        Returns:
            SendResult with statistics and failed emails
        """
        total_emails = len(email_contents)
        successful_sends = 0
        failed_sends = 0
        failed_emails = []
        sent_email_ids = []
        
        self.logger.info(f"Starting bulk email send for {total_emails} emails")
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_single_email(i: int, email_data: Dict[str, str]):
            """Send a single email with semaphore control."""
            nonlocal successful_sends, failed_sends
            
            async with semaphore:
                try:
                    recipient = email_data['recipient']
                    subject = email_data['subject']
                    body = email_data['body']
                    
                    # Send email with database tracking
                    result = await self.send_email(recipient, subject, body, track_in_database=True)
                    
                    if result['success']:
                        successful_sends += 1
                        if result['email_record_id']:
                            sent_email_ids.append(result['email_record_id'])
                    else:
                        failed_sends += 1
                        failed_emails.append({
                            'recipient': recipient,
                            'subject': subject,
                            'error': 'Failed to send email'
                        })
                    
                    # Report progress
                    if self.progress_callback:
                        progress = ((i + 1) / total_emails) * 100
                        self.progress_callback(progress, f"Sent {i + 1}/{total_emails} emails")
                    
                    # Small delay to avoid overwhelming SMTP server
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    failed_sends += 1
                    failed_emails.append({
                        'recipient': email_data.get('recipient', 'Unknown'),
                        'subject': email_data.get('subject', 'Unknown'),
                        'error': str(e)
                    })
                    self.logger.error(f"Failed to send email {i + 1}: {str(e)}")
        
        # Create tasks for all emails
        tasks = [
            send_single_email(i, email_data) 
            for i, email_data in enumerate(email_contents)
        ]
        
        # Execute all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        result = SendResult(
            total_emails=total_emails,
            successful_sends=successful_sends,
            failed_sends=failed_sends,
            failed_emails=failed_emails
        )
        
        self.logger.info(f"Bulk email send completed: {successful_sends}/{total_emails} successful")
        return result
    
    def test_smtp_connection(self) -> Dict[str, any]:
        """
        Test SMTP configuration and connection.
        
        Returns:
            Dictionary with test results and details
        """
        result = {
            'success': False,
            'message': '',
            'details': {}
        }
        
        try:
            # Test connection
            server = self._create_smtp_connection()
            server.quit()
            
            result['success'] = True
            result['message'] = 'SMTP connection test successful'
            result['details'] = {
                'server': self.smtp_config.server,
                'port': self.smtp_config.port,
                'email': self.smtp_config.email,
                'tls_enabled': self.smtp_config.use_tls
            }
            
            self.logger.info("SMTP connection test passed")
            
        except SMTPConnectionException as e:
            result['message'] = str(e)
            result['details'] = {'error_type': 'connection_error'}
            self.logger.error(f"SMTP connection test failed: {str(e)}")
        except Exception as e:
            result['message'] = f"Unexpected error during connection test: {str(e)}"
            result['details'] = {'error_type': 'unexpected_error'}
            self.logger.error(f"Unexpected error in SMTP test: {str(e)}")
        
        return result
    
    def get_provider_suggestions(self, email: str) -> Dict[str, any]:
        """
        Get suggested SMTP configuration for common email providers.
        
        Args:
            email: Email address to analyze
            
        Returns:
            Dictionary with suggested configuration or empty if not found
        """
        provider_config = self._get_provider_config(email)
        
        if provider_config:
            return {
                'suggested': True,
                'server': provider_config['server'],
                'port': provider_config['port'],
                'use_tls': provider_config['use_tls'],
                'provider': self._get_provider_name(email)
            }
        
        return {'suggested': False}
    
    def _get_provider_name(self, email: str) -> str:
        """Get provider name from email address."""
        domain = email.split('@')[1].lower()
        
        if 'gmail' in domain:
            return 'Gmail'
        elif 'outlook' in domain or 'hotmail' in domain or 'live' in domain:
            return 'Outlook/Hotmail'
        elif 'yahoo' in domain:
            return 'Yahoo'
        
        return 'Unknown'
    
    def get_email_history(self, status: Optional[str] = None, limit: Optional[int] = None) -> List[SentEmailModel]:
        """
        Get email sending history from database.
        
        Args:
            status: Optional status filter ('sent', 'failed', 'pending')
            limit: Optional limit on number of records
            
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
        try:
            stats = self.database_manager.get_database_stats()
            
            # Calculate additional statistics
            sent_emails_by_status = stats.get('sent_emails_by_status', {})
            total_sent = stats.get('sent_emails_count', 0)
            
            success_rate = 0.0
            if total_sent > 0:
                successful = sent_emails_by_status.get('sent', 0)
                success_rate = (successful / total_sent) * 100
            
            return {
                'total_emails_sent': total_sent,
                'successful_sends': sent_emails_by_status.get('sent', 0),
                'failed_sends': sent_emails_by_status.get('failed', 0),
                'pending_sends': sent_emails_by_status.get('pending', 0),
                'success_rate': round(success_rate, 2),
                'scraped_emails_available': stats.get('scraped_emails_count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get email statistics: {e}")
            return {
                'total_emails_sent': 0,
                'successful_sends': 0,
                'failed_sends': 0,
                'pending_sends': 0,
                'success_rate': 0.0,
                'scraped_emails_available': 0
            }
    
    def retry_failed_emails(self, limit: Optional[int] = None) -> Dict[str, any]:
        """
        Retry sending failed emails.
        
        Args:
            limit: Optional limit on number of emails to retry
            
        Returns:
            Dictionary with retry results
        """
        try:
            # Get failed emails from database
            failed_emails = self.database_manager.get_email_history(status='failed', limit=limit)
            
            if not failed_emails:
                return {
                    'success': True,
                    'message': 'No failed emails to retry',
                    'retried_count': 0,
                    'successful_retries': 0
                }
            
            successful_retries = 0
            
            for email_record in failed_emails:
                try:
                    # Update status to pending before retry
                    self.database_manager.update_email_status(email_record.id, 'pending')
                    
                    # Attempt to send email again
                    success = self._send_email_sync(
                        email_record.recipient_email,
                        email_record.subject,
                        email_record.body
                    )
                    
                    # Update status based on result
                    new_status = 'sent' if success else 'failed'
                    self.database_manager.update_email_status(email_record.id, new_status)
                    
                    if success:
                        successful_retries += 1
                    
                    # Small delay between retries
                    asyncio.sleep(0.2)
                    
                except Exception as e:
                    self.logger.error(f"Failed to retry email {email_record.id}: {e}")
                    self.database_manager.update_email_status(email_record.id, 'failed')
            
            return {
                'success': True,
                'message': f'Retried {len(failed_emails)} emails',
                'retried_count': len(failed_emails),
                'successful_retries': successful_retries
            }
            
        except Exception as e:
            self.logger.error(f"Failed to retry failed emails: {e}")
            return {
                'success': False,
                'message': f'Error retrying failed emails: {str(e)}',
                'retried_count': 0,
                'successful_retries': 0
            }
    
    def cleanup_old_records(self, days_old: int = 30) -> int:
        """
        Clean up old email records from database.
        
        Args:
            days_old: Number of days old records to keep
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM sent_emails 
                    WHERE sent_at < ? AND status IN ('sent', 'failed')
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old email records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {e}")
            return 0
    
    def __del__(self):
        """Cleanup thread pool on destruction."""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)