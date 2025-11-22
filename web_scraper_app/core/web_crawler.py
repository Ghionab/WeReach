"""
Advanced web crawler using crawl4ai for comprehensive website crawling
"""

import asyncio
import re
import logging
from typing import List, Set, Dict, Optional, Callable
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Simple test to see if this works
print("WebCrawler module loading...")

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
    print("crawl4ai imported successfully")
except ImportError as e:
    CRAWL4AI_AVAILABLE = False
    AsyncWebCrawler = None
    CrawlerRunConfig = None
    print(f"crawl4ai import failed: {e}")

try:
    from models.email_model import EmailModel
    print("EmailModel imported successfully")
except ImportError:
    try:
        from ..models.email_model import EmailModel
        print("EmailModel imported with relative import")
    except ImportError as e:
        print(f"EmailModel import failed: {e}")
        EmailModel = None


class CrawlerException(Exception):
    """Exception raised by the web crawler"""
    pass


class WebCrawler:
    """
    Advanced web crawler that discovers and crawls entire websites
    Uses crawl4ai for comprehensive crawling and email extraction
    """
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """Initialize the web crawler"""
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        # Email regex pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Crawler statistics
        self.stats = {
            'websites_crawled': 0,
            'pages_discovered': 0,
            'emails_found': 0,
            'subdomains_found': 0,
            'errors': 0
        }
        
        # Check if crawl4ai is available
        if not CRAWL4AI_AVAILABLE:
            self.logger.warning("crawl4ai not available, falling back to basic crawling")
    
    async def crawl_websites(self, urls: List[str]) -> List:
        """Crawl multiple websites comprehensively"""
        all_emails = []
        
        if not CRAWL4AI_AVAILABLE:
            # Fallback to basic scraping if crawl4ai is not available
            self.logger.warning("crawl4ai not available, using basic scraping fallback")
            return await self._fallback_scraping(urls)
        
        self.logger.info(f"Starting deep crawl of {len(urls)} websites")
        
        for i, url in enumerate(urls):
            try:
                # Normalize URL to ensure it has proper protocol
                normalized_url = self._normalize_url(url)
                
                if self.progress_callback:
                    self.progress_callback(i, len(urls), f"Deep crawling: {normalized_url}")
                
                website_emails = await self._crawl_single_website(normalized_url)
                all_emails.extend(website_emails)
                
                self.stats['websites_crawled'] += 1
                self.logger.info(f"Deep crawled {normalized_url} - Found {len(website_emails)} emails")
                
            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(f"Failed to deep crawl {url}: {str(e)}")
                continue
        
        self.logger.info(f"Deep crawling completed. Total emails found: {len(all_emails)}")
        return all_emails
    
    async def _fallback_scraping(self, urls: List[str]) -> List:
        """Fallback to basic scraping when crawl4ai is not available"""
        from .scraper import WebScraper
        
        scraper = WebScraper()
        all_emails = []
        
        for i, url in enumerate(urls):
            try:
                if self.progress_callback:
                    self.progress_callback(i, len(urls), f"Scraping (fallback): {url}")
                
                # Use the existing scraper as fallback
                emails = scraper.scrape_single_website(url)
                all_emails.extend(emails)
                
            except Exception as e:
                self.logger.error(f"Fallback scraping failed for {url}: {str(e)}")
                continue
        
        return all_emails
    
    async def _crawl_single_website(self, url: str) -> List:
        """Crawl a single website using crawl4ai"""
        emails = []
        
        self.logger.info(f"Starting to crawl: {url}")
        
        try:
            async with AsyncWebCrawler(verbose=True) as crawler:  # Enable verbose for debugging
                # Configure crawler for comprehensive crawling
                try:
                    from crawl4ai.cache_context import CacheMode
                    config = CrawlerRunConfig(
                        word_count_threshold=5,  # Lower threshold to capture more content
                        cache_mode=CacheMode.BYPASS,
                        process_iframes=True,
                        remove_overlay_elements=True,
                        simulate_user=True,
                        page_timeout=45000,  # Longer timeout
                        delay_before_return_html=3.0,  # Longer delay for dynamic content
                        js_code=[
                            # Scroll to load dynamic content
                            "window.scrollTo(0, document.body.scrollHeight);",
                            "await new Promise(resolve => setTimeout(resolve, 2000));",
                            # Try to trigger any lazy loading
                            "window.scrollTo(0, 0);",
                            "await new Promise(resolve => setTimeout(resolve, 1000));"
                        ]
                    )
                except ImportError:
                    # Fallback for older versions
                    config = CrawlerRunConfig(
                        word_count_threshold=5,
                        process_iframes=True,
                        remove_overlay_elements=True,
                        simulate_user=True,
                        page_timeout=45000,
                        delay_before_return_html=3.0
                    )
                
                self.logger.info(f"Crawling main page: {url}")
                
                # Crawl the main page
                result = await crawler.arun(url=url, config=config)
                
                if result.success:
                    self.logger.info(f"Successfully crawled {url}, content length: {len(result.cleaned_html) if result.cleaned_html else 0}")
                    
                    # Debug: Log some content to see what we got
                    if result.cleaned_html:
                        content_preview = result.cleaned_html[:500] + "..." if len(result.cleaned_html) > 500 else result.cleaned_html
                        self.logger.debug(f"Content preview: {content_preview}")
                    
                    # Extract emails from the page content
                    page_emails = self._extract_emails_from_content(result.cleaned_html, url)
                    emails.extend(page_emails)
                    
                    self.logger.info(f"Found {len(page_emails)} emails on main page")
                    
                    # Also try to extract from raw HTML if available
                    if hasattr(result, 'html') and result.html:
                        raw_emails = self._extract_emails_from_content(result.html, url)
                        emails.extend(raw_emails)
                        self.logger.info(f"Found {len(raw_emails)} additional emails from raw HTML")
                    
                    # Try to discover and crawl internal pages
                    if hasattr(result, 'links') and result.links:
                        internal_links = self._discover_internal_links(result.links, url)
                        self.logger.info(f"Discovered {len(internal_links)} internal links")
                        
                        # Crawl up to 10 internal pages for more comprehensive results
                        for i, internal_url in enumerate(list(internal_links)[:10]):
                            try:
                                self.logger.info(f"Crawling internal page {i+1}/10: {internal_url}")
                                internal_result = await crawler.arun(url=internal_url, config=config)
                                
                                if internal_result.success:
                                    internal_emails = self._extract_emails_from_content(
                                        internal_result.cleaned_html, internal_url
                                    )
                                    emails.extend(internal_emails)
                                    self.logger.info(f"Found {len(internal_emails)} emails on internal page")
                                    
                                    # Also check raw HTML for internal pages
                                    if hasattr(internal_result, 'html') and internal_result.html:
                                        raw_internal_emails = self._extract_emails_from_content(
                                            internal_result.html, internal_url
                                        )
                                        emails.extend(raw_internal_emails)
                                    
                                    # Small delay to be respectful
                                    await asyncio.sleep(2)
                                else:
                                    self.logger.warning(f"Failed to crawl internal page {internal_url}")
                                    
                            except Exception as e:
                                self.logger.warning(f"Error crawling internal page {internal_url}: {str(e)}")
                                continue
                    else:
                        self.logger.info("No links found or links attribute not available")
                
                else:
                    error_msg = result.error_message if hasattr(result, 'error_message') else 'Unknown error'
                    self.logger.error(f"Failed to crawl {url}: {error_msg}")
                    
                    # If crawl4ai fails, try fallback scraping
                    self.logger.info(f"Attempting fallback scraping for {url}")
                    fallback_emails = await self._fallback_scraping([url])
                    emails.extend(fallback_emails)
        
        except Exception as e:
            self.logger.error(f"Crawler error for {url}: {str(e)}")
            
            # Try fallback scraping if crawl4ai completely fails
            try:
                self.logger.info(f"Attempting fallback scraping due to crawler error for {url}")
                fallback_emails = await self._fallback_scraping([url])
                emails.extend(fallback_emails)
            except Exception as fallback_error:
                self.logger.error(f"Fallback scraping also failed for {url}: {str(fallback_error)}")
                raise CrawlerException(f"Both crawl4ai and fallback failed for {url}")
        
        # Remove duplicates and return
        unique_emails = self._remove_duplicate_emails(emails)
        self.stats['emails_found'] += len(unique_emails)
        
        self.logger.info(f"Total unique emails found for {url}: {len(unique_emails)}")
        return unique_emails
    
    def _discover_internal_links(self, links, base_url: str) -> Set[str]:
        """Discover internal links from crawled page"""
        internal_links = set()
        base_domain = urlparse(base_url).netloc
        
        try:
            # Handle different link formats
            if isinstance(links, dict):
                for link_type, link_list in links.items():
                    if isinstance(link_list, list):
                        for link in link_list:
                            href = link.get('href', '') if isinstance(link, dict) else str(link)
                            if href:
                                absolute_url = urljoin(base_url, href)
                                parsed_url = urlparse(absolute_url)
                                
                                # Only include internal links
                                if parsed_url.netloc == base_domain:
                                    internal_links.add(absolute_url)
            
        except Exception as e:
            self.logger.warning(f"Error discovering internal links: {str(e)}")
        
        return internal_links
    
    def _extract_emails_from_content(self, content: str, source_url: str) -> List:
        """Extract emails from HTML content"""
        emails = []
        
        if not content or not EmailModel:
            return emails
        
        # Find all email addresses
        found_emails = self.email_pattern.findall(content)
        
        for email in found_emails:
            # Skip common false positives
            if self._is_valid_email(email):
                email_model = EmailModel(
                    email=email.lower(),
                    source_website=source_url,
                    extracted_at=datetime.now()
                )
                emails.append(email_model)
        
        return emails
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate if email is likely to be real"""
        # Skip common false positives
        false_positives = {
            'example@example.com', 'test@test.com', 'admin@admin.com',
            'info@info.com', 'contact@contact.com', 'support@support.com',
            'noreply@noreply.com', 'no-reply@no-reply.com'
        }
        
        if email.lower() in false_positives:
            return False
        
        # Skip emails with suspicious patterns
        suspicious_patterns = [
            r'@(localhost|127\.0\.0\.1|example\.com|test\.com)',
            r'@.*\.(png|jpg|gif|css|js)$',
            r'^(test|example|sample|demo)@',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False
        
        return True
    
    def _remove_duplicate_emails(self, emails: List) -> List:
        """Remove duplicate emails while preserving the first occurrence"""
        if not emails or not EmailModel:
            return emails
            
        seen_emails = set()
        unique_emails = []
        
        for email in emails:
            email_key = (email.email.lower(), email.source_website)
            if email_key not in seen_emails:
                seen_emails.add(email_key)
                unique_emails.append(email)
        
        return unique_emails
    
    def get_crawling_stats(self) -> Dict:
        """Get crawling statistics"""
        return self.stats.copy()
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it has proper protocol"""
        url = url.strip()
        
        # Add https:// if no protocol is specified
        if not url.startswith(('http://', 'https://', 'file://', 'raw:')):
            url = f"https://{url}"
        
        return url


print("WebCrawler class defined successfully")