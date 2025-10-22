"""
Database manager for the web scraper application using SQLite.
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager
from pathlib import Path

from models import EmailModel, SentEmailModel


class DatabaseException(Exception):
    """Database operation errors."""
    pass


class DatabaseManager:
    """Manages SQLite database operations for the web scraper application."""
    
    def __init__(self, db_path: str = "scraper_data.db"):
        """Initialize database manager with specified database path."""
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise DatabaseException(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self):
        """Create database tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create scraped emails table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraped_emails (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        source_website TEXT NOT NULL,
                        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create sent emails history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sent_emails (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recipient_email TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        body TEXT NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'pending'))
                    )
                """)
                
                # Create configuration table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scraped_emails_email 
                    ON scraped_emails(email)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scraped_emails_website 
                    ON scraped_emails(source_website)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sent_emails_recipient 
                    ON sent_emails(recipient_email)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sent_emails_status 
                    ON sent_emails(status)
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise DatabaseException(f"Database initialization failed: {e}")
    
    def save_scraped_emails(self, emails: List[EmailModel]) -> int:
        """
        Store scraped emails with duplicate prevention.
        Returns the number of new emails saved.
        """
        if not emails:
            return 0
            
        saved_count = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for email_model in emails:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO scraped_emails 
                            (email, source_website, extracted_at)
                            VALUES (?, ?, ?)
                        """, (
                            email_model.email,
                            email_model.source_website,
                            email_model.extracted_at
                        ))
                        
                        if cursor.rowcount > 0:
                            saved_count += 1
                            
                    except sqlite3.Error as e:
                        self.logger.warning(f"Failed to save email {email_model.email}: {e}")
                        continue
                
                conn.commit()
                self.logger.info(f"Saved {saved_count} new emails out of {len(emails)} total")
                return saved_count
                
        except Exception as e:
            self.logger.error(f"Failed to save scraped emails: {e}")
            raise DatabaseException(f"Failed to save scraped emails: {e}")
    
    def get_scraped_emails(self, website: Optional[str] = None) -> List[EmailModel]:
        """
        Retrieve all scraped emails, optionally filtered by website.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if website:
                    cursor.execute("""
                        SELECT id, email, source_website, extracted_at
                        FROM scraped_emails
                        WHERE source_website = ?
                        ORDER BY extracted_at DESC
                    """, (website,))
                else:
                    cursor.execute("""
                        SELECT id, email, source_website, extracted_at
                        FROM scraped_emails
                        ORDER BY extracted_at DESC
                    """)
                
                rows = cursor.fetchall()
                emails = []
                
                for row in rows:
                    email_model = EmailModel(
                        email=row['email'],
                        source_website=row['source_website'],
                        extracted_at=datetime.fromisoformat(row['extracted_at']),
                        id=row['id']
                    )
                    emails.append(email_model)
                
                return emails
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve scraped emails: {e}")
            raise DatabaseException(f"Failed to retrieve scraped emails: {e}")
    
    def save_sent_email(self, email_record: SentEmailModel) -> int:
        """
        Store sent email history record.
        Returns the ID of the saved record.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO sent_emails 
                    (recipient_email, subject, body, sent_at, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    email_record.recipient_email,
                    email_record.subject,
                    email_record.body,
                    email_record.sent_at,
                    email_record.status
                ))
                
                email_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Saved sent email record with ID: {email_id}")
                return email_id
                
        except Exception as e:
            self.logger.error(f"Failed to save sent email record: {e}")
            raise DatabaseException(f"Failed to save sent email record: {e}")
    
    def get_email_history(self, status: Optional[str] = None, limit: Optional[int] = None) -> List[SentEmailModel]:
        """
        Retrieve sent email history, optionally filtered by status.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, recipient_email, subject, body, sent_at, status
                    FROM sent_emails
                """
                params = []
                
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                
                query += " ORDER BY sent_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                email_history = []
                for row in rows:
                    sent_email = SentEmailModel(
                        recipient_email=row['recipient_email'],
                        subject=row['subject'],
                        body=row['body'],
                        sent_at=datetime.fromisoformat(row['sent_at']),
                        status=row['status'],
                        id=row['id']
                    )
                    email_history.append(sent_email)
                
                return email_history
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve email history: {e}")
            raise DatabaseException(f"Failed to retrieve email history: {e}")
    
    def search_sent_emails(self, search_term: str, status: Optional[str] = None) -> List[SentEmailModel]:
        """
        Search sent emails by recipient email or subject.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, recipient_email, subject, body, sent_at, status
                    FROM sent_emails
                    WHERE (recipient_email LIKE ? OR subject LIKE ?)
                """
                params = [f"%{search_term}%", f"%{search_term}%"]
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY sent_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                email_history = []
                for row in rows:
                    sent_email = SentEmailModel(
                        recipient_email=row['recipient_email'],
                        subject=row['subject'],
                        body=row['body'],
                        sent_at=datetime.fromisoformat(row['sent_at']),
                        status=row['status'],
                        id=row['id']
                    )
                    email_history.append(sent_email)
                
                return email_history
                
        except Exception as e:
            self.logger.error(f"Failed to search sent emails: {e}")
            raise DatabaseException(f"Failed to search sent emails: {e}")
    
    def update_email_status(self, email_id: int, status: str) -> bool:
        """
        Update the status of a sent email record.
        """
        if status not in ['sent', 'failed', 'pending']:
            raise ValueError(f"Invalid status: {status}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE sent_emails 
                    SET status = ?
                    WHERE id = ?
                """, (status, email_id))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    self.logger.info(f"Updated email {email_id} status to {status}")
                else:
                    self.logger.warning(f"No email found with ID: {email_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to update email status: {e}")
            raise DatabaseException(f"Failed to update email status: {e}")
    
    def get_email_count_by_website(self) -> dict:
        """
        Get count of scraped emails grouped by website.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT source_website, COUNT(*) as email_count
                    FROM scraped_emails
                    GROUP BY source_website
                    ORDER BY email_count DESC
                """)
                
                rows = cursor.fetchall()
                return {row['source_website']: row['email_count'] for row in rows}
                
        except Exception as e:
            self.logger.error(f"Failed to get email count by website: {e}")
            raise DatabaseException(f"Failed to get email count by website: {e}")
    
    def search_emails(self, search_term: str) -> List[EmailModel]:
        """
        Search scraped emails by email address or website.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, email, source_website, extracted_at
                    FROM scraped_emails
                    WHERE email LIKE ? OR source_website LIKE ?
                    ORDER BY extracted_at DESC
                """, (f"%{search_term}%", f"%{search_term}%"))
                
                rows = cursor.fetchall()
                emails = []
                
                for row in rows:
                    email_model = EmailModel(
                        email=row['email'],
                        source_website=row['source_website'],
                        extracted_at=datetime.fromisoformat(row['extracted_at']),
                        id=row['id']
                    )
                    emails.append(email_model)
                
                return emails
                
        except Exception as e:
            self.logger.error(f"Failed to search emails: {e}")
            raise DatabaseException(f"Failed to search emails: {e}")
    
    def clear_scraped_emails(self) -> int:
        """
        Clear all scraped emails from the database.
        Returns the number of deleted records.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM scraped_emails")
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleared {deleted_count} scraped emails")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to clear scraped emails: {e}")
            raise DatabaseException(f"Failed to clear scraped emails: {e}")
    
    def clear_all_data(self) -> dict:
        """
        Clear all data from the database.
        Returns a dictionary with the number of deleted records.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear scraped emails
                cursor.execute("DELETE FROM scraped_emails")
                scraped_deleted = cursor.rowcount
                
                # Clear sent emails
                cursor.execute("DELETE FROM sent_emails")
                sent_deleted = cursor.rowcount
                
                # Clear config (optional - keep configuration)
                # cursor.execute("DELETE FROM config")
                # config_deleted = cursor.rowcount
                
                conn.commit()
                
                result = {
                    'scraped_emails_deleted': scraped_deleted,
                    'sent_emails_deleted': sent_deleted
                }
                
                self.logger.info(f"Cleared all data: {result}")
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to clear all data: {e}")
            raise DatabaseException(f"Failed to clear all data: {e}")
    
    def get_database_stats(self) -> dict:
        """
        Get database statistics.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get scraped emails count
                cursor.execute("SELECT COUNT(*) as count FROM scraped_emails")
                scraped_count = cursor.fetchone()['count']
                
                # Get sent emails count
                cursor.execute("SELECT COUNT(*) as count FROM sent_emails")
                sent_count = cursor.fetchone()['count']
                
                # Get sent emails by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM sent_emails 
                    GROUP BY status
                """)
                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'scraped_emails_count': scraped_count,
                    'sent_emails_count': sent_count,
                    'sent_emails_by_status': status_counts
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            raise DatabaseException(f"Failed to get database stats: {e}")