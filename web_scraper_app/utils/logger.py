"""
Comprehensive logging configuration for the web scraper application.
Provides structured logging with different levels and output formats.
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import traceback

from .exceptions import BaseScraperException, ErrorSeverity


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        # Add custom fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format the message
        formatted = super().format(record)
        
        # Add color to level name
        formatted = formatted.replace(
            record.levelname,
            f"{color}{record.levelname}{reset}"
        )
        
        return formatted


class ScraperLogger:
    """
    Centralized logging manager for the web scraper application.
    Provides structured logging with file rotation and different output formats.
    """
    
    def __init__(self, app_name: str = "WebScraperApp", log_dir: Optional[str] = None):
        """
        Initialize the logging system.
        
        Args:
            app_name: Name of the application for logging context
            log_dir: Directory to store log files (defaults to logs/ in current directory)
        """
        self.app_name = app_name
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.root_logger.handlers.clear()
        
        # Setup handlers
        self._setup_file_handlers()
        self._setup_console_handler()
        
        # Create application logger
        self.logger = logging.getLogger(app_name)
        
    def _setup_file_handlers(self):
        """Setup file handlers with rotation."""
        # Main application log (INFO and above)
        app_log_file = self.log_dir / f"{self.app_name.lower()}.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.root_logger.addHandler(app_handler)
        
        # Error log (ERROR and above)
        error_log_file = self.log_dir / f"{self.app_name.lower()}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'Module: %(module)s, Function: %(funcName)s, Line: %(lineno)d\n'
            '%(message)s\n' + '-' * 80
        ))
        self.root_logger.addHandler(error_handler)
        
        # Debug log (DEBUG and above) - only in debug mode
        if os.getenv('DEBUG', '').lower() in ('true', '1', 'yes'):
            debug_log_file = self.log_dir / f"{self.app_name.lower()}_debug.log"
            debug_handler = logging.handlers.RotatingFileHandler(
                debug_log_file,
                maxBytes=20 * 1024 * 1024,  # 20MB
                backupCount=2,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(JSONFormatter())
            self.root_logger.addHandler(debug_handler)
    
    def _setup_console_handler(self):
        """Setup console handler with colored output."""
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Set console log level based on environment
        if os.getenv('DEBUG', '').lower() in ('true', '1', 'yes'):
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)
            
        # Use colored formatter for console
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        self.root_logger.addHandler(console_handler)
    
    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log an exception with full context and user-friendly handling.
        
        Args:
            exception: The exception to log
            context: Additional context information
        """
        context = context or {}
        
        # Create log entry with exception details
        log_data = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "context": context
        }
        
        # Add custom exception data if available
        if isinstance(exception, BaseScraperException):
            log_data.update({
                "user_message": exception.user_message,
                "error_code": exception.error_code,
                "severity": exception.severity.value,
                "details": exception.details
            })
            
            # Log at appropriate level based on severity
            if exception.severity == ErrorSeverity.CRITICAL:
                self.logger.critical(
                    f"Critical error: {exception}",
                    exc_info=True,
                    extra={"extra_fields": log_data}
                )
            elif exception.severity == ErrorSeverity.HIGH:
                self.logger.error(
                    f"High severity error: {exception}",
                    exc_info=True,
                    extra={"extra_fields": log_data}
                )
            elif exception.severity == ErrorSeverity.MEDIUM:
                self.logger.warning(
                    f"Medium severity error: {exception}",
                    exc_info=True,
                    extra={"extra_fields": log_data}
                )
            else:  # LOW severity
                self.logger.info(
                    f"Low severity error: {exception}",
                    extra={"extra_fields": log_data}
                )
        else:
            # Standard exception logging
            self.logger.error(
                f"Unhandled exception: {exception}",
                exc_info=True,
                extra={"extra_fields": log_data}
            )
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation with context."""
        self.logger.info(
            f"Starting operation: {operation}",
            extra={"extra_fields": {"operation": operation, "parameters": kwargs}}
        )
    
    def log_operation_end(self, operation: str, success: bool = True, **kwargs):
        """Log the end of an operation with results."""
        status = "completed successfully" if success else "failed"
        level = logging.INFO if success else logging.ERROR
        
        self.logger.log(
            level,
            f"Operation {operation} {status}",
            extra={"extra_fields": {"operation": operation, "success": success, "results": kwargs}}
        )
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics for operations."""
        self.logger.info(
            f"Performance - {operation}: {duration:.2f}s",
            extra={"extra_fields": {
                "operation": operation,
                "duration_seconds": duration,
                "metrics": metrics
            }}
        )
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, **details):
        """Log user actions for audit trail."""
        self.logger.info(
            f"User action: {action}",
            extra={"extra_fields": {
                "action": action,
                "user_id": user_id,
                "details": details
            }}
        )
    
    def log_security_event(self, event: str, severity: str = "medium", **details):
        """Log security-related events."""
        log_level = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }.get(severity.lower(), logging.WARNING)
        
        self.logger.log(
            log_level,
            f"Security event: {event}",
            extra={"extra_fields": {
                "security_event": event,
                "severity": severity,
                "details": details
            }}
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module."""
        return logging.getLogger(f"{self.app_name}.{name}")
    
    def set_log_level(self, level: str):
        """Set the logging level dynamically."""
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.root_logger.setLevel(numeric_level)
        
        # Update console handler level
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(numeric_level)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files."""
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.logger.info(f"Cleaned up old log file: {log_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up log file {log_file}: {e}")


# Global logger instance
_global_logger: Optional[ScraperLogger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. Creates global logger if not exists.
    
    Args:
        name: Logger name (module name)
        
    Returns:
        Logger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = ScraperLogger()
    
    if name:
        return _global_logger.get_logger(name)
    else:
        return _global_logger.logger


def setup_logging(app_name: str = "WebScraperApp", log_dir: Optional[str] = None) -> ScraperLogger:
    """
    Setup application logging.
    
    Args:
        app_name: Application name
        log_dir: Log directory path
        
    Returns:
        ScraperLogger instance
    """
    global _global_logger
    _global_logger = ScraperLogger(app_name, log_dir)
    return _global_logger


def log_exception(exception: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Convenience function to log exceptions.
    
    Args:
        exception: Exception to log
        context: Additional context
    """
    logger = get_logger()
    if hasattr(logger, 'log_exception'):
        # Use ScraperLogger method if available
        _global_logger.log_exception(exception, context)
    else:
        # Fallback to standard logging
        logger.error(f"Exception occurred: {exception}", exc_info=True)