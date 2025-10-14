"""
Web scraping module with Playwright integration for email extraction.
"""
import asyncio
import re
import logging
import time
from typing import List, Callable, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

from models.email_model import EmailModel
from utils.retry_manager import (
    RetryConfig, RetryStrategy, async_retry_on_failure, 
    with_async_fallback, get_fallback_manager
)
from utils.exceptions import NetworkException, RetryableException


class ScraperException(Exception):
    """Base exception for scraper operations."""
    pass


class NetworkException(ScraperException):
    """Network-related errors during scraping."""
    pass


class ValidationException(ScraperException):
    """URL validation errors."""
    pass


class RetryableException(ScraperException):
    """Exceptions that can be retried."""
    pass


class WebScraper:
    """
    Web scraper class that uses Playwright for dynamic content and BeautifulSoup for parsing.
    Extracts email addresses from websites with progress reporting and error handling.
    """
    
    # Email regex pattern as specified in requirements
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    def __init__(self, progress_callback: Optional[Callable[[int, int, str], None]] = None,
                 log_callback: Optional[Callable[[str], None]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: int = 30):
        """
        Initialize the WebScraper.
        
        Args:
            progress_callback: Callback function for progress updates (current, total, message)
            log_callback: Callback function for log messages
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Base delay between retries in seconds (exponential backoff)
            timeout: Request timeout in seconds
        """
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        
        # Register fallback mechanisms
        self._register_fallbacks()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_browser()
        
    async def _initialize_browser(self):
        """Initialize Playwright browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self._log("Browser initialized successfully")
        except Exception as e:
            self._log(f"Failed to initialize browser: {str(e)}")
            raise
            
    async def _cleanup_browser(self):
        """Clean up browser resources."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self._log("Browser cleanup completed")
        except Exception as e:
            self._log(f"Error during browser cleanup: {str(e)}")
            
    def _log(self, message: str):
        """Log message using callback or logger."""
        self.logger.info(message)
        if self.log_callback:
            self.log_callback(message)
            
    def _update_progress(self, current: int, total: int, message: str):
        """Update progress using callback."""
        if self.progress_callback:
            self.progress_callback(current, total, message)
    
    def _register_fallbacks(self):
        """Register fallback mechanisms for scraping operations."""
        fallback_manager = get_fallback_manager()
        
        # Register fallback for page content scraping
        fallback_manager.register_fallback(
            "scrape_page_content",
            self._fallback_scrape_with_requests,
            priority=1
        )
        
        # Register fallback for single website scraping
        fallback_manager.register_fallback(
            "scrape_single_website", 
            self._fallback_scrape_basic,
            priority=1
        )
    
    async def _fallback_scrape_with_requests(self, url: str) -> str:
        """
        Fallback method using requests library when Playwright fails.
        
        Args:
            url: URL to scrape
            
        Returns:
            Page content as string
        """
        try:
            import aiohttp
            import asyncio
            
            self._log(f"Using fallback HTTP client for: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout / 1000)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status >= 400:
                        raise NetworkException(f"HTTP {response.status} error for {url}")
                    
                    content = await response.text()
                    
                    if not content or len(content) < 100:
                        raise RetryableException(f"Received minimal content from {url}")
                    
                    return content
                    
        except ImportError:
            raise Exception("aiohttp not available for fallback scraping")
        except Exception as e:
            self._log(f"Fallback scraping failed for {url}: {e}")
            raise
    
    async def _fallback_scrape_basic(self, url: str) -> List[str]:
        """
        Basic fallback scraping that returns empty list on failure.
        
        Args:
            url: URL to scrape
            
        Returns:
            Empty list (graceful degradation)
        """
        self._log(f"Using basic fallback for {url} - returning empty results")
        return []
            
    def _validate_url(self, url: str) -> str:
        """
        Validate and normalize URL with comprehensive validation.
        
        Args:
            url: URL to validate
            
        Returns:
            Normalized URL
            
        Raises:
            ValidationException: If URL is invalid
        """
        if not url or not url.strip():
            raise ValidationException("URL cannot be empty")
            
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            # Validate URL format
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValidationException(f"Invalid URL format: {url}")
                
            # Check for valid domain format
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) < 2:
                raise ValidationException(f"Invalid domain format: {parsed.netloc}")
                
            # Check for suspicious URLs
            suspicious_patterns = [
                r'localhost',
                r'127\.0\.0\.1',
                r'0\.0\.0\.0',
                r'192\.168\.',
                r'10\.',
                r'172\.(1[6-9]|2[0-9]|3[01])\.'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, parsed.netloc, re.IGNORECASE):
                    self._log(f"Warning: Suspicious URL detected: {url}")
                    
            return url
            
        except Exception as e:
            if isinstance(e, ValidationException):
                raise
            raise ValidationException(f"URL validation failed: {str(e)}")
            
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry mechanism.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (PlaywrightTimeoutError, NetworkException, RetryableException) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    self._log(f"All {self.max_retries + 1} attempts failed. Last error: {str(e)}")
                    break
                    
                # Calculate delay with exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                self._log(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f} seconds...")
                
                await asyncio.sleep(delay)
                
        raise last_exception or Exception("All retry attempts failed")
        
    def extract_emails(self, text: str) -> List[str]:
        """
        Extract email addresses from text using regex pattern.
        
        Args:
            text: Text content to search for emails
            
        Returns:
            List of unique email addresses found
        """
        if not text:
            return []
            
        # Find all email matches
        matches = re.findall(self.EMAIL_PATTERN, text, re.IGNORECASE)
        
        # Remove duplicates and filter out common false positives
        unique_emails = set()
        for email in matches:
            email = email.lower().strip()
            # Skip common false positives
            if not self._is_valid_email_address(email):
                continue
            unique_emails.add(email)
            
        return list(unique_emails)
        
    def _is_valid_email_address(self, email: str) -> bool:
        """
        Additional validation for extracted email addresses.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email appears to be valid
        """
        # Skip common false positives
        false_positives = [
            'example@example.com',
            'test@test.com',
            'admin@localhost',
            'user@domain.com',
            'info@example.org'
        ]
        
        if email in false_positives:
            return False
            
        # Skip emails with suspicious patterns
        suspicious_patterns = [
            r'\.png$', r'\.jpg$', r'\.gif$', r'\.css$', r'\.js$',
            r'@\d+\.\d+\.\d+\.\d+',  # IP addresses
            r'@localhost',
            r'@example\.',
            r'@test\.',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False
                
        return True
        
    @async_retry_on_failure(RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retryable_exceptions=(NetworkException, RetryableException, PlaywrightTimeoutError)
    ))
    @with_async_fallback("scrape_page_content")
    async def _scrape_page_content(self, url: str) -> str:
        """
        Internal method to scrape page content with error handling.
        
        Args:
            url: Normalized URL to scrape
            
        Returns:
            Page content as string
            
        Raises:
            NetworkException: For network-related errors
            RetryableException: For retryable errors
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")
            
        page = None
        try:
            # Create new page
            page = await self.browser.new_page()
            
            # Set user agent and headers to avoid bot detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Set viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            self._log(f"Navigating to: {url}")
            
            # Navigate to page with timeout
            response = await page.goto(
                url, 
                wait_until='domcontentloaded', 
                timeout=self.timeout
            )
            
            # Check response status
            if response and response.status >= 400:
                if response.status in [429, 503, 502, 504]:
                    raise RetryableException(f"Server error {response.status} for {url}")
                else:
                    raise NetworkException(f"HTTP {response.status} error for {url}")
            
            # Wait for page to load completely
            await page.wait_for_timeout(2000)
            
            # Get page content
            content = await page.content()
            
            if not content or len(content) < 100:
                raise RetryableException(f"Received empty or minimal content from {url}")
                
            return content
            
        except PlaywrightTimeoutError as e:
            raise RetryableException(f"Timeout while loading {url}: {str(e)}")
        except Exception as e:
            if isinstance(e, (NetworkException, RetryableException)):
                raise
            # Convert other exceptions to retryable for potential retry
            raise RetryableException(f"Error loading {url}: {str(e)}")
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass  # Ignore cleanup errors

    @with_async_fallback("scrape_single_website")
    async def scrape_single_website(self, url: str) -> List[str]:
        """
        Scrape a single website for email addresses with retry mechanism.
        
        Args:
            url: Website URL to scrape
            
        Returns:
            List of email addresses found on the website
            
        Raises:
            ValidationException: If URL is invalid
            ScraperException: If scraping fails after all retries
        """
        # Validate URL
        normalized_url = self._validate_url(url)
        
        try:
            # Use retry mechanism for scraping
            content = await self._retry_with_backoff(self._scrape_page_content, normalized_url)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
                
            # Extract text content
            text_content = soup.get_text()
            
            # Extract emails from text
            emails = self.extract_emails(text_content)
            
            self._log(f"Successfully scraped {normalized_url} - Found {len(emails)} emails")
            return emails
            
        except ValidationException:
            # Re-raise validation errors without retry
            raise
        except Exception as e:
            error_msg = f"Failed to scrape {normalized_url} after {self.max_retries + 1} attempts: {str(e)}"
            self._log(error_msg)
            raise ScraperException(error_msg) from e
                
    async def scrape_websites(self, urls: List[str]) -> List[EmailModel]:
        """
        Scrape multiple websites for email addresses with comprehensive error handling.
        
        Args:
            urls: List of website URLs to scrape
            
        Returns:
            List of EmailModel objects with scraped emails
        """
        if not urls:
            self._log("No URLs provided for scraping")
            return []
            
        # Validate all URLs first
        valid_urls = []
        invalid_urls = []
        
        for url in urls:
            try:
                normalized_url = self._validate_url(url)
                valid_urls.append((url, normalized_url))
            except ValidationException as e:
                invalid_urls.append((url, str(e)))
                self._log(f"Invalid URL skipped: {url} - {str(e)}")
                
        if invalid_urls:
            self._log(f"Skipped {len(invalid_urls)} invalid URLs")
            
        if not valid_urls:
            self._log("No valid URLs to scrape")
            return []
            
        all_emails = []
        total_urls = len(valid_urls)
        successful_scrapes = 0
        failed_scrapes = 0
        
        self._log(f"Starting to scrape {total_urls} valid websites")
        self._update_progress(0, total_urls, "Starting scraping process...")
        
        for i, (original_url, normalized_url) in enumerate(valid_urls, 1):
            try:
                self._update_progress(i, total_urls, f"Scraping: {original_url}")
                
                # Scrape single website
                emails = await self.scrape_single_website(original_url)
                
                # Convert to EmailModel objects
                current_time = datetime.now()
                
                for email in emails:
                    try:
                        email_model = EmailModel(
                            email=email,
                            source_website=normalized_url,
                            extracted_at=current_time
                        )
                        all_emails.append(email_model)
                    except ValueError as e:
                        self._log(f"Invalid email data skipped: {email} - {str(e)}")
                        continue
                        
                successful_scrapes += 1
                self._log(f"Completed {i}/{total_urls}: {original_url} - Found {len(emails)} emails")
                
            except ValidationException as e:
                # This shouldn't happen since we pre-validated, but handle it
                failed_scrapes += 1
                self._log(f"Validation error for {original_url}: {str(e)}")
                continue
                
            except ScraperException as e:
                # Scraping failed after retries
                failed_scrapes += 1
                self._log(f"Scraping failed for {original_url}: {str(e)}")
                continue
                
            except Exception as e:
                # Unexpected error
                failed_scrapes += 1
                self._log(f"Unexpected error scraping {original_url}: {str(e)}")
                continue
                
        # Final progress update and summary
        completion_message = f"Scraping completed. Found {len(all_emails)} total emails from {successful_scrapes}/{total_urls} websites"
        self._update_progress(total_urls, total_urls, completion_message)
        
        # Log detailed summary
        self._log(f"Scraping Summary:")
        self._log(f"  - Total URLs processed: {total_urls}")
        self._log(f"  - Successful scrapes: {successful_scrapes}")
        self._log(f"  - Failed scrapes: {failed_scrapes}")
        self._log(f"  - Invalid URLs skipped: {len(invalid_urls)}")
        self._log(f"  - Total emails found: {len(all_emails)}")
        
        return all_emails


    def get_scraping_stats(self) -> Dict[str, Any]:
        """
        Get scraping statistics and configuration.
        
        Returns:
            Dictionary with scraper configuration and stats
        """
        return {
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'timeout_ms': self.timeout,
            'email_pattern': self.EMAIL_PATTERN,
            'browser_initialized': self.browser is not None
        }
        
    async def test_connection(self, test_url: str = "https://httpbin.org/html") -> bool:
        """
        Test scraper connection and functionality.
        
        Args:
            test_url: URL to test with (default is a reliable test endpoint)
            
        Returns:
            True if test successful, False otherwise
        """
        try:
            self._log(f"Testing scraper connection with: {test_url}")
            
            if not self.browser:
                await self._initialize_browser()
                
            content = await self._scrape_page_content(test_url)
            
            if content and len(content) > 0:
                self._log("Scraper connection test successful")
                return True
            else:
                self._log("Scraper connection test failed: No content received")
                return False
                
        except Exception as e:
            self._log(f"Scraper connection test failed: {str(e)}")
            return False


# Convenience function for one-off scraping
async def scrape_websites_simple(urls: List[str], 
                                progress_callback: Optional[Callable[[int, int, str], None]] = None,
                                log_callback: Optional[Callable[[str], None]] = None,
                                max_retries: int = 3,
                                retry_delay: float = 1.0,
                                timeout: int = 30) -> List[EmailModel]:
    """
    Simple function to scrape websites without managing the scraper instance.
    
    Args:
        urls: List of URLs to scrape
        progress_callback: Optional progress callback
        log_callback: Optional log callback
        max_retries: Maximum retry attempts
        retry_delay: Base retry delay in seconds
        timeout: Request timeout in seconds
        
    Returns:
        List of EmailModel objects with scraped emails
    """
    async with WebScraper(
        progress_callback=progress_callback, 
        log_callback=log_callback,
        max_retries=max_retries,
        retry_delay=retry_delay,
        timeout=timeout
    ) as scraper:
        return await scraper.scrape_websites(urls)


# URL validation utility function
def validate_urls(urls: List[str]) -> tuple[List[str], List[tuple[str, str]]]:
    """
    Validate a list of URLs and return valid and invalid ones.
    
    Args:
        urls: List of URLs to validate
        
    Returns:
        Tuple of (valid_urls, invalid_urls_with_errors)
    """
    valid_urls = []
    invalid_urls = []
    
    # Create a temporary scraper instance for validation
    scraper = WebScraper()
    
    for url in urls:
        try:
            normalized_url = scraper._validate_url(url)
            valid_urls.append(normalized_url)
        except ValidationException as e:
            invalid_urls.append((url, str(e)))
            
    return valid_urls, invalid_urls