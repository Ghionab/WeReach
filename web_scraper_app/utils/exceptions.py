"""
Comprehensive exception hierarchy for the web scraper application.
Provides custom exception classes for different error types and user-friendly error messages.
"""
from typing import Dict, Optional, Any, List
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for categorizing exceptions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BaseScraperException(Exception):
    """
    Base exception class for all scraper application errors.
    Provides common functionality for error handling and user-friendly messages.
    """
    
    def __init__(self, message: str, user_message: Optional[str] = None, 
                 error_code: Optional[str] = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize base exception.
        
        Args:
            message: Technical error message for logging
            user_message: User-friendly error message for display
            error_code: Unique error code for tracking
            severity: Error severity level
            details: Additional error details for debugging
        """
        super().__init__(message)
        self.user_message = user_message or self._get_default_user_message()
        self.error_code = error_code or self._get_default_error_code()
        self.severity = severity
        self.details = details or {}
        
    def _get_default_user_message(self) -> str:
        """Get default user-friendly message for this exception type."""
        return "An unexpected error occurred. Please try again."
        
    def _get_default_error_code(self) -> str:
        """Get default error code for this exception type."""
        return f"{self.__class__.__name__.upper()}_001"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "user_message": self.user_message,
            "error_code": self.error_code,
            "severity": self.severity.value,
            "details": self.details
        }


# Web Scraping Exceptions
class ScraperException(BaseScraperException):
    """Base exception for web scraping operations."""
    
    def _get_default_user_message(self) -> str:
        return "An error occurred while scraping websites. Please check your URLs and try again."


class NetworkException(ScraperException):
    """Network-related errors during scraping."""
    
    def __init__(self, message: str, url: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.url = url
        if url:
            self.details["url"] = url
            
    def _get_default_user_message(self) -> str:
        if self.url:
            return f"Unable to connect to {self.url}. Please check your internet connection and try again."
        return "Network connection failed. Please check your internet connection and try again."
        
    def _get_default_error_code(self) -> str:
        return "NETWORK_001"


class ValidationException(ScraperException):
    """URL validation and input validation errors."""
    
    def __init__(self, message: str, invalid_input: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.invalid_input = invalid_input
        if invalid_input:
            self.details["invalid_input"] = invalid_input
            
    def _get_default_user_message(self) -> str:
        if self.invalid_input:
            return f"Invalid input: {self.invalid_input}. Please check and try again."
        return "Invalid input provided. Please check your data and try again."
        
    def _get_default_error_code(self) -> str:
        return "VALIDATION_001"


class RetryableException(ScraperException):
    """Exceptions that can be retried with exponential backoff."""
    
    def __init__(self, message: str, retry_count: int = 0, max_retries: int = 3, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.details.update({"retry_count": retry_count, "max_retries": max_retries})
        
    def _get_default_user_message(self) -> str:
        return f"Operation failed (attempt {self.retry_count + 1}/{self.max_retries + 1}). Retrying..."
        
    def _get_default_error_code(self) -> str:
        return "RETRYABLE_001"


# AI Service Exceptions
class AIException(BaseScraperException):
    """Base exception for AI service related errors."""
    
    def _get_default_user_message(self) -> str:
        return "AI service error occurred. Please check your API key and try again."


class AIAuthenticationException(AIException):
    """Exception for API authentication errors."""
    
    def _get_default_user_message(self) -> str:
        return "AI API authentication failed. Please check your API key in settings."
        
    def _get_default_error_code(self) -> str:
        return "AI_AUTH_001"


class AIQuotaException(AIException):
    """Exception for API quota/rate limit errors."""
    
    def _get_default_user_message(self) -> str:
        return "AI API quota exceeded or rate limit reached. Please try again later."
        
    def _get_default_error_code(self) -> str:
        return "AI_QUOTA_001"


class AIServiceUnavailableException(AIException):
    """Exception for AI service unavailability."""
    
    def _get_default_user_message(self) -> str:
        return "AI service is currently unavailable. Please try again later."
        
    def _get_default_error_code(self) -> str:
        return "AI_SERVICE_001"


# Email Service Exceptions
class EmailException(BaseScraperException):
    """Base exception for email operations."""
    
    def _get_default_user_message(self) -> str:
        return "Email operation failed. Please check your email settings and try again."


class SMTPConnectionException(EmailException):
    """Exception for SMTP connection issues."""
    
    def __init__(self, message: str, smtp_server: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.smtp_server = smtp_server
        if smtp_server:
            self.details["smtp_server"] = smtp_server
            
    def _get_default_user_message(self) -> str:
        if self.smtp_server:
            return f"Unable to connect to email server {self.smtp_server}. Please check your SMTP settings."
        return "Unable to connect to email server. Please check your SMTP settings."
        
    def _get_default_error_code(self) -> str:
        return "SMTP_CONNECTION_001"


class EmailSendException(EmailException):
    """Exception for individual email sending failures."""
    
    def __init__(self, message: str, recipient: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.recipient = recipient
        if recipient:
            self.details["recipient"] = recipient
            
    def _get_default_user_message(self) -> str:
        if self.recipient:
            return f"Failed to send email to {self.recipient}. Please check the email address."
        return "Failed to send email. Please check the recipient address."
        
    def _get_default_error_code(self) -> str:
        return "EMAIL_SEND_001"


class EmailAuthenticationException(EmailException):
    """Exception for email authentication failures."""
    
    def _get_default_user_message(self) -> str:
        return "Email authentication failed. Please check your email credentials in settings."
        
    def _get_default_error_code(self) -> str:
        return "EMAIL_AUTH_001"


# Database Exceptions
class DatabaseException(BaseScraperException):
    """Base exception for database operations."""
    
    def _get_default_user_message(self) -> str:
        return "Database error occurred. Please try again or restart the application."


class DatabaseConnectionException(DatabaseException):
    """Exception for database connection issues."""
    
    def _get_default_user_message(self) -> str:
        return "Unable to connect to database. Please restart the application."
        
    def _get_default_error_code(self) -> str:
        return "DB_CONNECTION_001"


class DatabaseIntegrityException(DatabaseException):
    """Exception for database integrity violations."""
    
    def _get_default_user_message(self) -> str:
        return "Data integrity error. The operation could not be completed."
        
    def _get_default_error_code(self) -> str:
        return "DB_INTEGRITY_001"


# Configuration Exceptions
class ConfigurationException(BaseScraperException):
    """Base exception for configuration-related errors."""
    
    def _get_default_user_message(self) -> str:
        return "Configuration error. Please check your settings."


class InvalidConfigurationException(ConfigurationException):
    """Exception for invalid configuration values."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        if config_key:
            self.details["config_key"] = config_key
            
    def _get_default_user_message(self) -> str:
        if self.config_key:
            return f"Invalid configuration for {self.config_key}. Please check your settings."
        return "Invalid configuration detected. Please check your settings."
        
    def _get_default_error_code(self) -> str:
        return "CONFIG_INVALID_001"


class MissingConfigurationException(ConfigurationException):
    """Exception for missing required configuration."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        if config_key:
            self.details["config_key"] = config_key
            
    def _get_default_user_message(self) -> str:
        if self.config_key:
            return f"Missing required configuration: {self.config_key}. Please configure it in settings."
        return "Missing required configuration. Please check your settings."
        
    def _get_default_error_code(self) -> str:
        return "CONFIG_MISSING_001"


# Export/Import Exceptions
class ExportException(BaseScraperException):
    """Base exception for export operations."""
    
    def _get_default_user_message(self) -> str:
        return "Export operation failed. Please try again or choose a different location."


class FilePermissionException(ExportException):
    """Exception for file permission errors."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        if file_path:
            self.details["file_path"] = file_path
            
    def _get_default_user_message(self) -> str:
        if self.file_path:
            return f"Permission denied for file {self.file_path}. Please choose a different location."
        return "Permission denied. Please choose a different file location."
        
    def _get_default_error_code(self) -> str:
        return "FILE_PERMISSION_001"


class DiskSpaceException(ExportException):
    """Exception for insufficient disk space."""
    
    def _get_default_user_message(self) -> str:
        return "Insufficient disk space. Please free up space and try again."
        
    def _get_default_error_code(self) -> str:
        return "DISK_SPACE_001"


# Application Exceptions
class ApplicationException(BaseScraperException):
    """Base exception for general application errors."""
    
    def _get_default_user_message(self) -> str:
        return "Application error occurred. Please restart the application."


class InitializationException(ApplicationException):
    """Exception for application initialization failures."""
    
    def _get_default_user_message(self) -> str:
        return "Application failed to initialize properly. Please restart the application."
        
    def _get_default_error_code(self) -> str:
        return "APP_INIT_001"


class ResourceException(ApplicationException):
    """Exception for resource-related errors (memory, CPU, etc.)."""
    
    def _get_default_user_message(self) -> str:
        return "System resources are low. Please close other applications and try again."
        
    def _get_default_error_code(self) -> str:
        return "RESOURCE_001"


# Error Message Translation System
class ErrorMessageTranslator:
    """
    Translates technical error messages to user-friendly messages.
    Provides centralized error message management.
    """
    
    # Error message mappings for common technical errors
    ERROR_MAPPINGS = {
        # Network errors
        "Connection refused": "Unable to connect to the server. Please check your internet connection.",
        "Timeout": "The operation timed out. Please try again.",
        "Name or service not known": "Unable to resolve the website address. Please check the URL.",
        "SSL": "Secure connection failed. The website may have security issues.",
        
        # Database errors
        "database is locked": "Database is busy. Please wait a moment and try again.",
        "no such table": "Database structure error. Please restart the application.",
        "UNIQUE constraint failed": "This data already exists in the database.",
        
        # File system errors
        "Permission denied": "Permission denied. Please check file permissions or choose a different location.",
        "No space left on device": "Insufficient disk space. Please free up space and try again.",
        "File not found": "The specified file could not be found.",
        
        # API errors
        "401": "Authentication failed. Please check your API key.",
        "403": "Access forbidden. Please check your API permissions.",
        "429": "Rate limit exceeded. Please wait and try again.",
        "500": "Server error. Please try again later.",
        "503": "Service unavailable. Please try again later.",
    }
    
    @classmethod
    def translate_error(cls, technical_message: str) -> str:
        """
        Translate technical error message to user-friendly message.
        
        Args:
            technical_message: The technical error message
            
        Returns:
            User-friendly error message
        """
        technical_lower = technical_message.lower()
        
        for pattern, user_message in cls.ERROR_MAPPINGS.items():
            if pattern.lower() in technical_lower:
                return user_message
                
        # If no specific mapping found, return a generic message
        return "An unexpected error occurred. Please try again or contact support if the problem persists."
    
    @classmethod
    def get_error_suggestions(cls, error_type: str) -> List[str]:
        """
        Get troubleshooting suggestions based on error type.
        
        Args:
            error_type: The type of error that occurred
            
        Returns:
            List of troubleshooting suggestions
        """
        suggestions = {
            "NetworkException": [
                "Check your internet connection",
                "Verify the website URL is correct",
                "Try again in a few minutes",
                "Check if the website is accessible in your browser"
            ],
            "AIAuthenticationException": [
                "Verify your API key is correct",
                "Check if your API key has expired",
                "Ensure you have sufficient API credits",
                "Test the API connection in settings"
            ],
            "SMTPConnectionException": [
                "Check your email server settings",
                "Verify your email credentials",
                "Ensure your firewall allows email connections",
                "Try using a different SMTP port"
            ],
            "DatabaseException": [
                "Restart the application",
                "Check if the database file is corrupted",
                "Ensure sufficient disk space",
                "Check file permissions"
            ],
            "ValidationException": [
                "Check your input format",
                "Ensure all required fields are filled",
                "Verify URLs are properly formatted",
                "Remove any special characters"
            ]
        }
        
        return suggestions.get(error_type, [
            "Try the operation again",
            "Restart the application",
            "Check your settings",
            "Contact support if the problem persists"
        ])