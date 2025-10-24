"""
Email data models for the web scraper application.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re
from urllib.parse import urlparse


@dataclass
class EmailModel:
    """Model for scraped email addresses."""
    email: str
    source_website: str
    extracted_at: datetime
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate email format after initialization."""
        if not self.is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        if not self.is_valid_url(self.source_website):
            raise ValueError(f"Invalid URL format: {self.source_website}")
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format using regex pattern."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


@dataclass
class SentEmailModel:
    """Model for sent email history."""
    recipient_email: str
    subject: str
    body: str
    sent_at: datetime
    status: str
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate sent email data after initialization."""
        if not EmailModel.is_valid_email(self.recipient_email):
            raise ValueError(f"Invalid recipient email format: {self.recipient_email}")
        if not self.subject.strip():
            raise ValueError("Email subject cannot be empty")
        if not self.body.strip():
            raise ValueError("Email body cannot be empty")
        if self.status not in ['sent', 'failed', 'pending']:
            raise ValueError(f"Invalid status: {self.status}. Must be 'sent', 'failed', or 'pending'")


@dataclass
class SMTPConfig:
    """Model for SMTP configuration."""
    server: str
    port: int
    email: str
    password: str
    use_tls: bool = True
    
    def __post_init__(self):
        """Validate SMTP configuration after initialization."""
        if not self.server.strip():
            raise ValueError("SMTP server cannot be empty")
        if not isinstance(self.port, int) or self.port <= 0 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}. Must be between 1 and 65535")
        if not EmailModel.is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        if not self.password.strip():
            raise ValueError("SMTP password cannot be empty")
    
    def test_connection_params(self) -> dict:
        """Return connection parameters for testing."""
        return {
            'server': self.server,
            'port': self.port,
            'email': self.email,
            'use_tls': self.use_tls
        }


@dataclass
class EmailContent:
    """Model for AI-generated email content."""
    subject: str
    body: str
    website: str
    
    def __post_init__(self):
        """Validate email content after initialization."""
        if not self.subject.strip():
            raise ValueError("Email subject cannot be empty")
        if not self.body.strip():
            raise ValueError("Email body cannot be empty")
        if not EmailModel.is_valid_url(self.website):
            raise ValueError(f"Invalid website URL format: {self.website}")
    
    def get_formatted_content(self) -> dict:
        """Return formatted email content for sending."""
        return {
            'subject': self.subject.strip(),
            'body': self.body.strip(),
            'website': self.website
        }