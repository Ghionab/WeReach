"""
Input validation utilities for the web scraper application.
Provides comprehensive validation for emails, URLs, and configuration parameters.
"""
import re
import ipaddress
from typing import List, Tuple, Optional, Union
from urllib.parse import urlparse
import html
import bleach


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, is_valid: bool, message: str = "", sanitized_value: Optional[str] = None):
        self.is_valid = is_valid
        self.message = message
        self.sanitized_value = sanitized_value
    
    def __bool__(self) -> bool:
        return self.is_valid


class EmailValidator:
    """Validator for email addresses."""
    
    # Comprehensive email regex pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Common email providers for additional validation
    COMMON_PROVIDERS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'icloud.com', 'protonmail.com', 'mail.com'
    }
    
    @classmethod
    def validate(cls, email: str) -> ValidationResult:
        """
        Validate email address format and structure.
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult with validation status and message
        """
        if not email or not isinstance(email, str):
            return ValidationResult(False, "Email cannot be empty")
        
        # Sanitize input
        sanitized_email = cls.sanitize_email(email)
        
        # Check length constraints
        if len(sanitized_email) > 254:  # RFC 5321 limit
            return ValidationResult(False, "Email address too long (max 254 characters)")
        
        # Check basic format
        if not cls.EMAIL_PATTERN.match(sanitized_email):
            return ValidationResult(False, "Invalid email format")
        
        # Split into local and domain parts
        local_part, domain_part = sanitized_email.rsplit('@', 1)
        
        # Validate local part
        local_validation = cls._validate_local_part(local_part)
        if not local_validation.is_valid:
            return local_validation
        
        # Validate domain part
        domain_validation = cls._validate_domain_part(domain_part)
        if not domain_validation.is_valid:
            return domain_validation
        
        return ValidationResult(True, "Valid email address", sanitized_email)
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """
        Sanitize email input by removing dangerous characters.
        
        Args:
            email: Raw email input
            
        Returns:
            Sanitized email string
        """
        if not email:
            return ""
        
        # Remove whitespace and convert to lowercase
        sanitized = email.strip().lower()
        
        # HTML escape to prevent injection
        sanitized = html.escape(sanitized)
        
        # Remove any null bytes or control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
        
        return sanitized
    
    @classmethod
    def _validate_local_part(cls, local_part: str) -> ValidationResult:
        """Validate the local part of an email address."""
        if not local_part:
            return ValidationResult(False, "Email local part cannot be empty")
        
        if len(local_part) > 64:  # RFC 5321 limit
            return ValidationResult(False, "Email local part too long (max 64 characters)")
        
        # Check for consecutive dots
        if '..' in local_part:
            return ValidationResult(False, "Email cannot contain consecutive dots")
        
        # Check for dots at start or end
        if local_part.startswith('.') or local_part.endswith('.'):
            return ValidationResult(False, "Email cannot start or end with a dot")
        
        return ValidationResult(True)
    
    @classmethod
    def _validate_domain_part(cls, domain_part: str) -> ValidationResult:
        """Validate the domain part of an email address."""
        if not domain_part:
            return ValidationResult(False, "Email domain cannot be empty")
        
        if len(domain_part) > 253:  # RFC 1035 limit
            return ValidationResult(False, "Email domain too long (max 253 characters)")
        
        # Check for valid domain format
        domain_pattern = re.compile(r'^[a-zA-Z0-9.-]+$')
        if not domain_pattern.match(domain_part):
            return ValidationResult(False, "Invalid characters in email domain")
        
        # Check domain parts
        parts = domain_part.split('.')
        if len(parts) < 2:
            return ValidationResult(False, "Email domain must have at least one dot")
        
        for part in parts:
            if not part:
                return ValidationResult(False, "Email domain cannot have empty parts")
            if len(part) > 63:
                return ValidationResult(False, "Email domain part too long (max 63 characters)")
            if part.startswith('-') or part.endswith('-'):
                return ValidationResult(False, "Email domain parts cannot start or end with hyphen")
        
        return ValidationResult(True)
    
    @classmethod
    def validate_multiple(cls, emails: List[str]) -> List[Tuple[str, ValidationResult]]:
        """
        Validate multiple email addresses.
        
        Args:
            emails: List of email addresses to validate
            
        Returns:
            List of tuples containing (email, ValidationResult)
        """
        results = []
        for email in emails:
            result = cls.validate(email)
            results.append((email, result))
        return results


class URLValidator:
    """Validator for URLs."""
    
    # Allowed URL schemes
    ALLOWED_SCHEMES = {'http', 'https'}
    
    # Dangerous URL patterns to block
    DANGEROUS_PATTERNS = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'file:',
        r'ftp:'
    ]
    
    @classmethod
    def validate(cls, url: str) -> ValidationResult:
        """
        Validate URL format and security.
        
        Args:
            url: URL to validate
            
        Returns:
            ValidationResult with validation status and message
        """
        if not url or not isinstance(url, str):
            return ValidationResult(False, "URL cannot be empty")
        
        # Sanitize input
        sanitized_url = cls.sanitize_url(url)
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, sanitized_url, re.IGNORECASE):
                return ValidationResult(False, f"Potentially dangerous URL scheme detected")
        
        # Parse URL
        try:
            parsed = urlparse(sanitized_url)
        except Exception:
            return ValidationResult(False, "Invalid URL format")
        
        # Check required components
        if not parsed.scheme:
            return ValidationResult(False, "URL must include a scheme (http/https)")
        
        if not parsed.netloc:
            return ValidationResult(False, "URL must include a domain")
        
        # Check allowed schemes
        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            return ValidationResult(False, f"URL scheme must be one of: {', '.join(cls.ALLOWED_SCHEMES)}")
        
        # Validate domain
        domain_validation = cls._validate_domain(parsed.netloc)
        if not domain_validation.is_valid:
            return domain_validation
        
        # Check URL length
        if len(sanitized_url) > 2048:  # Common browser limit
            return ValidationResult(False, "URL too long (max 2048 characters)")
        
        return ValidationResult(True, "Valid URL", sanitized_url)
    
    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """
        Sanitize URL input.
        
        Args:
            url: Raw URL input
            
        Returns:
            Sanitized URL string
        """
        if not url:
            return ""
        
        # Remove whitespace
        sanitized = url.strip()
        
        # Add scheme if missing
        if not sanitized.startswith(('http://', 'https://')):
            sanitized = 'https://' + sanitized
        
        # HTML escape to prevent injection
        sanitized = html.escape(sanitized, quote=False)
        
        # Remove any null bytes or control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
        
        return sanitized
    
    @classmethod
    def _validate_domain(cls, netloc: str) -> ValidationResult:
        """Validate the domain part of a URL."""
        # Extract hostname (remove port if present)
        hostname = netloc.split(':')[0]
        
        if not hostname:
            return ValidationResult(False, "URL domain cannot be empty")
        
        # Check for IP addresses
        try:
            ipaddress.ip_address(hostname)
            # IP addresses are valid but we might want to warn about them
            return ValidationResult(True, "URL uses IP address")
        except ValueError:
            pass  # Not an IP address, continue with domain validation
        
        # Check domain format
        if len(hostname) > 253:
            return ValidationResult(False, "Domain name too long")
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
            return ValidationResult(False, "Invalid characters in domain name")
        
        # Check domain parts
        parts = hostname.split('.')
        if len(parts) < 2:
            return ValidationResult(False, "Domain must have at least one dot")
        
        for part in parts:
            if not part:
                return ValidationResult(False, "Domain cannot have empty parts")
            if len(part) > 63:
                return ValidationResult(False, "Domain part too long")
            if part.startswith('-') or part.endswith('-'):
                return ValidationResult(False, "Domain parts cannot start or end with hyphen")
        
        return ValidationResult(True)
    
    @classmethod
    def validate_multiple(cls, urls: List[str]) -> List[Tuple[str, ValidationResult]]:
        """
        Validate multiple URLs.
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            List of tuples containing (url, ValidationResult)
        """
        results = []
        for url in urls:
            result = cls.validate(url)
            results.append((url, result))
        return results


class ConfigValidator:
    """Validator for configuration parameters."""
    
    @classmethod
    def validate_smtp_server(cls, server: str) -> ValidationResult:
        """Validate SMTP server hostname."""
        if not server or not isinstance(server, str):
            return ValidationResult(False, "SMTP server cannot be empty")
        
        sanitized = server.strip()
        
        # Check length
        if len(sanitized) > 253:
            return ValidationResult(False, "SMTP server name too long")
        
        # Check for valid hostname format
        if not re.match(r'^[a-zA-Z0-9.-]+$', sanitized):
            return ValidationResult(False, "Invalid characters in SMTP server name")
        
        return ValidationResult(True, "Valid SMTP server", sanitized)
    
    @classmethod
    def validate_smtp_port(cls, port: Union[str, int]) -> ValidationResult:
        """Validate SMTP port number."""
        try:
            port_num = int(port)
        except (ValueError, TypeError):
            return ValidationResult(False, "SMTP port must be a number")
        
        if port_num < 1 or port_num > 65535:
            return ValidationResult(False, "SMTP port must be between 1 and 65535")
        
        # Common SMTP ports
        common_ports = {25, 465, 587, 2525}
        if port_num not in common_ports:
            return ValidationResult(True, f"Warning: {port_num} is not a common SMTP port", str(port_num))
        
        return ValidationResult(True, "Valid SMTP port", str(port_num))
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> ValidationResult:
        """Validate API key format."""
        if not api_key or not isinstance(api_key, str):
            return ValidationResult(False, "API key cannot be empty")
        
        sanitized = api_key.strip()
        
        # Check length (most API keys are at least 20 characters)
        if len(sanitized) < 10:
            return ValidationResult(False, "API key appears too short")
        
        # Check for suspicious characters
        if any(char in sanitized for char in '<>"\'&'):
            return ValidationResult(False, "API key contains invalid characters")
        
        return ValidationResult(True, "Valid API key format", sanitized)


class InputSanitizer:
    """General input sanitization utilities."""
    
    @classmethod
    def sanitize_text_input(cls, text: str, max_length: int = 1000) -> str:
        """
        Sanitize general text input.
        
        Args:
            text: Raw text input
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text string
        """
        if not text:
            return ""
        
        # Remove dangerous HTML tags and attributes
        sanitized = bleach.clean(text, tags=[], attributes={}, strip=True)
        
        # Remove control characters except common whitespace
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
        
        # Trim to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename for safe file operations.
        
        Args:
            filename: Raw filename input
            
        Returns:
            Sanitized filename string
        """
        if not filename:
            return "untitled"
        
        # Remove path separators and dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        sanitized = ''.join(char for char in filename if char not in dangerous_chars)
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        # Trim whitespace and dots (Windows doesn't like trailing dots)
        sanitized = sanitized.strip('. ')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "untitled"
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized


# Convenience functions for common validation tasks
def validate_email(email: str) -> ValidationResult:
    """Validate a single email address."""
    return EmailValidator.validate(email)


def validate_url(url: str) -> ValidationResult:
    """Validate a single URL."""
    return URLValidator.validate(url)


def validate_emails_from_csv_content(content: str) -> List[Tuple[str, ValidationResult]]:
    """
    Validate emails extracted from CSV content.
    
    Args:
        content: CSV file content as string
        
    Returns:
        List of tuples containing (email, ValidationResult)
    """
    import csv
    import io
    
    results = []
    
    try:
        # Parse CSV content
        csv_reader = csv.reader(io.StringIO(content))
        
        for row_num, row in enumerate(csv_reader, 1):
            for col_num, cell in enumerate(row):
                # Check if cell looks like an email
                if '@' in cell and '.' in cell:
                    validation = validate_email(cell)
                    results.append((f"Row {row_num}, Col {col_num}: {cell}", validation))
    
    except Exception as e:
        results.append(("CSV parsing error", ValidationResult(False, f"Error parsing CSV: {e}")))
    
    return results


def validate_urls_from_csv_content(content: str) -> List[Tuple[str, ValidationResult]]:
    """
    Validate URLs extracted from CSV content.
    
    Args:
        content: CSV file content as string
        
    Returns:
        List of tuples containing (url, ValidationResult)
    """
    import csv
    import io
    
    results = []
    
    try:
        # Parse CSV content
        csv_reader = csv.reader(io.StringIO(content))
        
        for row_num, row in enumerate(csv_reader, 1):
            for col_num, cell in enumerate(row):
                # Check if cell looks like a URL
                if any(cell.strip().startswith(scheme) for scheme in ['http://', 'https://', 'www.']):
                    validation = validate_url(cell)
                    results.append((f"Row {row_num}, Col {col_num}: {cell}", validation))
    
    except Exception as e:
        results.append(("CSV parsing error", ValidationResult(False, f"Error parsing CSV: {e}")))
    
    return results