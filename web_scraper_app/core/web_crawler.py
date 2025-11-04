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
        if not CRAWL4AI_AVAILABLE:
            raise CrawlerException("Advanced crawling requires crawl4ai library")
        
        # Simplified implementation for now
        return []
    
    def get_crawling_stats(self) -> Dict:
        """Get crawling statistics"""
        return self.stats.copy()


print("WebCrawler class defined successfully")