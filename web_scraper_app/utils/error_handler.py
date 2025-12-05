"""
Centralized error handling system for the web scraper application.
Provides user-friendly error handling, reporting, and recovery mechanisms.
"""
import sys
import traceback
from typing import Optional, Callable, Dict, Any, List
from functools import wraps
from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal

from .exceptions import (
    BaseScraperException, ErrorSeverity, ErrorMessageTranslator,
    NetworkException, ValidationException, AIException, EmailException,
    DatabaseException, ConfigurationException, ApplicationException
)
from .logger import get_logger, log_exception


class ErrorHandler(QObject):
    """
    Centralized error handler that manages error display, logging, and recovery.
    Integrates with PyQt6 for user-friendly error dialogs.
    """
    
    # Signals for error events
    error_occurred = pyqtSignal(object)  # Emitted when an error occurs
    critical_error = pyqtSignal(object)  # Emitted for critical errors
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        """
        Initialize error handler.
        
        Args:
            parent_widget: Parent widget for error dialogs
        """
        super().__init__()
        self.parent_widget = parent_widget
        self.logger = get_logger("ErrorHandler")
        self.error_count = 0
        self.recent_errors: List[Dict[str, Any]] = []
        self.max_recent_errors = 50
        
        # Error recovery callbacks
        self.recovery_callbacks: Dict[str, Callable] = {}
        
    def handle_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None,
                        show_dialog: bool = True, auto_recover: bool = True) -> bool:
        """
        Handle an exception with logging, user notification, and optional recovery.
        
        Args:
            exception: The exception to handle
            context: Additional context information
            show_dialog: Whether to show error dialog to user
            auto_recover: Whether to attempt automatic recovery
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        self.error_count += 1
        context = context or {}
        
        # Log the exception
        log_exception(exception, context)
        
        # Add to recent errors
        error_info = {
            "timestamp": self._get_timestamp(),
            "exception": exception,
            "context": context,
            "error_count": self.error_count
        }
        self.recent_errors.append(error_info)
        
        # Keep only recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # Emit error signal
        self.error_occurred.emit(exception)
        
        # Handle critical errors
        if isinstance(exception, BaseScraperException) and exception.severity == ErrorSeverity.CRITICAL:
            self.critical_error.emit(exception)
            
        # Show user dialog if requested
        if show_dialog:
            self._show_error_dialog(exception, context)
            
        # Attempt recovery if enabled
        recovery_success = False
        if auto_recover:
            recovery_success = self._attempt_recovery(exception, context)
            
        return recovery_success
    
    def _show_error_dialog(self, exception: Exception, context: Dict[str, Any]):
        """Show user-friendly error dialog."""
        if not self.parent_widget:
            return
            
        # Determine dialog type and message
        if isinstance(exception, BaseScraperException):
            title = self._get_error_title(exception)
            message = exception.user_message
            details = self._format_error_details(exception, context)
            icon = self._get_error_icon(exception.severity)
        else:
            title = "Unexpected Error"
            message = ErrorMessageTranslator.translate_error(str(exception))
            details = f"Technical details: {str(exception)}"
            icon = QMessageBox.Icon.Critical
            
        # Create message box
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        # Add suggestions if available
        suggestions = self._get_error_suggestions(exception)
        if suggestions:
            suggestion_text = "\n\nSuggestions:\n" + "\n".join(f"• {s}" for s in suggestions)
            msg_box.setText(message + suggestion_text)
            
        # Add detailed information
        if details:
            msg_box.setDetailedText(details)
            
        # Add appropriate buttons
        if isinstance(exception, BaseScraperException) and exception.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Retry)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Retry)
        else:
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
        msg_box.exec()
    
    def _get_error_title(self, exception: BaseScraperException) -> str:
        """Get appropriate title for error dialog."""
        severity_titles = {
            ErrorSeverity.LOW: "Information",
            ErrorSeverity.MEDIUM: "Warning", 
            ErrorSeverity.HIGH: "Error",
            ErrorSeverity.CRITICAL: "Critical Error"
        }
        return severity_titles.get(exception.severity, "Error")
    
    def _get_error_icon(self, severity: ErrorSeverity) -> QMessageBox.Icon:
        """Get appropriate icon for error severity."""
        severity_icons = {
            ErrorSeverity.LOW: QMessageBox.Icon.Information,
            ErrorSeverity.MEDIUM: QMessageBox.Icon.Warning,
            ErrorSeverity.HIGH: QMessageBox.Icon.Critical,
            ErrorSeverity.CRITICAL: QMessageBox.Icon.Critical
        }
        return severity_icons.get(severity, QMessageBox.Icon.Warning)
    
    def _format_error_details(self, exception: BaseScraperException, context: Dict[str, Any]) -> str:
        """Format detailed error information."""
        details = [
            f"Error Code: {exception.error_code}",
            f"Error Type: {type(exception).__name__}",
            f"Severity: {exception.severity.value}",
        ]
        
        if exception.details:
            details.append("Error Details:")
            for key, value in exception.details.items():
                details.append(f"  {key}: {value}")
                
        if context:
            details.append("Context:")
            for key, value in context.items():
                details.append(f"  {key}: {value}")
                
        details.append(f"\nTechnical Message: {str(exception)}")
        
        return "\n".join(details)
    
    def _get_error_suggestions(self, exception: Exception) -> List[str]:
        """Get troubleshooting suggestions for the error."""
        if isinstance(exception, BaseScraperException):
            return ErrorMessageTranslator.get_error_suggestions(type(exception).__name__)
        else:
            return ErrorMessageTranslator.get_error_suggestions("UnknownException")
    
    def _attempt_recovery(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Attempt automatic recovery from the error."""
        exception_type = type(exception).__name__
        
        if exception_type in self.recovery_callbacks:
            try:
                self.logger.info(f"Attempting recovery for {exception_type}")
                recovery_callback = self.recovery_callbacks[exception_type]
                return recovery_callback(exception, context)
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed for {exception_type}: {recovery_error}")
                return False
                
        return False
    
    def register_recovery_callback(self, exception_type: str, callback: Callable[[Exception, Dict[str, Any]], bool]):
        """
        Register a recovery callback for a specific exception type.
        
        Args:
            exception_type: Name of the exception class
            callback: Recovery function that returns True if recovery succeeded
        """
        self.recovery_callbacks[exception_type] = callback
        self.logger.info(f"Registered recovery callback for {exception_type}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        error_types = {}
        for error_info in self.recent_errors:
            error_type = type(error_info["exception"]).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        return {
            "total_errors": self.error_count,
            "recent_errors": len(self.recent_errors),
            "error_types": error_types,
            "last_error": self.recent_errors[-1] if self.recent_errors else None
        }
    
    def clear_error_history(self):
        """Clear the error history."""
        self.recent_errors.clear()
        self.error_count = 0
        self.logger.info("Error history cleared")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(parent_widget: Optional[QWidget] = None) -> ErrorHandler:
    """
    Get global error handler instance.
    
    Args:
        parent_widget: Parent widget for error dialogs
        
    Returns:
        ErrorHandler instance
    """
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(parent_widget)
    elif parent_widget and not _global_error_handler.parent_widget:
        _global_error_handler.parent_widget = parent_widget
        
    return _global_error_handler


def handle_error(exception: Exception, context: Optional[Dict[str, Any]] = None,
                show_dialog: bool = True, auto_recover: bool = True) -> bool:
    """
    Convenience function to handle errors using global error handler.
    
    Args:
        exception: Exception to handle
        context: Additional context
        show_dialog: Whether to show error dialog
        auto_recover: Whether to attempt recovery
        
    Returns:
        True if handled successfully
    """
    error_handler = get_error_handler()
    return error_handler.handle_exception(exception, context, show_dialog, auto_recover)


def error_handler_decorator(show_dialog: bool = True, auto_recover: bool = True,
                          context_func: Optional[Callable] = None):
    """
    Decorator for automatic error handling in functions.
    
    Args:
        show_dialog: Whether to show error dialog
        auto_recover: Whether to attempt recovery
        context_func: Function to generate context information
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {}
                if context_func:
                    try:
                        context = context_func(*args, **kwargs)
                    except Exception:
                        pass
                        
                context.update({
                    "function": func.__name__,
                    "module": func.__module__,
                    "args": str(args)[:200],  # Limit length
                    "kwargs": str(kwargs)[:200]
                })
                
                handle_error(e, context, show_dialog, auto_recover)
                return None
                
        return wrapper
    return decorator


def setup_global_exception_handler():
    """Setup global exception handler for unhandled exceptions."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle unhandled exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to work normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Log the unhandled exception
        logger = get_logger("GlobalExceptionHandler")
        logger.critical(
            "Unhandled exception occurred",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Handle with error handler
        exception = exc_value if exc_value else exc_type()
        context = {
            "unhandled": True,
            "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        }
        
        handle_error(exception, context, show_dialog=True, auto_recover=False)
    
    # Set the global exception handler
    sys.excepthook = handle_exception


class ErrorReporter:
    """Utility class for reporting errors to external services or files."""
    
    def __init__(self, report_file: Optional[str] = None):
        """
        Initialize error reporter.
        
        Args:
            report_file: File to write error reports to
        """
        self.report_file = report_file
        self.logger = get_logger("ErrorReporter")
    
    def report_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None,
                    user_feedback: Optional[str] = None):
        """
        Report error for analysis or external tracking.
        
        Args:
            exception: Exception to report
            context: Additional context
            user_feedback: Optional user feedback about the error
        """
        report_data = {
            "timestamp": self._get_timestamp(),
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "context": context or {},
            "user_feedback": user_feedback,
            "system_info": self._get_system_info()
        }
        
        if isinstance(exception, BaseScraperException):
            report_data.update({
                "error_code": exception.error_code,
                "severity": exception.severity.value,
                "user_message": exception.user_message,
                "details": exception.details
            })
        
        # Write to file if configured
        if self.report_file:
            try:
                import json
                with open(self.report_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(report_data) + '\n')
            except Exception as e:
                self.logger.error(f"Failed to write error report: {e}")
        
        self.logger.info(f"Error reported: {report_data['exception_type']}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        import platform
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture()[0]
        }