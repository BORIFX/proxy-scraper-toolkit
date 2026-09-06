"""Core scraper implementation with resilience features."""

import time
import logging
from typing import Optional, Dict, List
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import ScraperConfig, setup_logging
from .proxy import ProxyRotator, Proxy


logger = logging.getLogger(__name__)


class Scraper:
    """Resilient web scraper with proxy rotation, rate limiting, and robots.txt checking."""
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize scraper.
        
        Args:
            config: ScraperConfig instance (uses defaults if not provided)
        """
        self.config = config or ScraperConfig()
        self.logger = setup_logging(
            log_level=self.config.log_level,
            log_file=self.config.log_file
        )
        
        self.proxy_rotator: Optional[ProxyRotator] = None
        self.robots_parsers: Dict[str, RobotFileParser] = {}
        self.last_request_time = 0
        
        self._setup_session()
        self.logger.info("Scraper initialized")
    
    def _setup_session(self):
        """Set up requests session with retry strategy."""
        self.session = requests.Session()
        
        # Retry strategy for transient failures
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set user agent
        if self.config.user_agent:
            self.session.headers.update({"User-Agent": self.config.user_agent})
        
        # Add custom headers
        if self.config.custom_headers:
            self.session.headers.update(self.config.custom_headers)
    
    def set_proxies(self, proxies: List[str], strategy: str = "round_robin"):
        """
        Set up proxy rotation.
        
        Args:
            proxies: List of proxy URLs
            strategy: Rotation strategy ("round_robin", "random", "weighted")
        """
        self.proxy_rotator = ProxyRotator(proxies, strategy=strategy)
        self.logger.info(f"Proxies configured: {len(proxies)} proxies, strategy={strategy}")
    
    def _can_fetch(self, url: str) -> bool:
        """Check if we're allowed to fetch this URL based on robots.txt."""
        if not self.config.respect_robots_txt:
            return True
        
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            if domain not in self.robots_parsers:
                # Fetch and cache robots.txt for this domain
                robot_parser = RobotFileParser()
                robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
                robot_parser.set_url(robots_url)
                robot_parser.read()
                self.robots_parsers[domain] = robot_parser
            
            allowed = self.robots_parsers[domain].can_fetch("*", url)
            if not allowed:
                self.logger.warning(f"robots.txt disallows: {url}")
            return allowed
        
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            # Allow by default if robots.txt check fails
            return True
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.request_delay:
            sleep_time = self.config.request_delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def fetch(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Fetch a URL with retries, rate limiting, and proxy rotation.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments to pass to requests.get()
        
        Returns:
            Response object if successful, None otherwise
        """
        # Check robots.txt
        if not self._can_fetch(url):
            self.logger.error(f"Skipping URL (robots.txt): {url}")
            return None
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Prepare request kwargs
        request_kwargs = {
            "timeout": self.config.timeout,
            **kwargs
        }
        
        # Add proxy if configured
        proxy: Optional[Proxy] = None
        if self.config.use_proxies and self.proxy_rotator:
            proxy = self.proxy_rotator.get_next()
            request_kwargs["proxies"] = self.proxy_rotator.get_proxy_dict(proxy)
        
        # Make request with retries handled by session
        try:
            self.logger.info(f"Fetching: {url}" + (f" via {proxy.url}" if proxy else ""))
            response = self.session.get(url, **request_kwargs)
            response.raise_for_status()
            
            if proxy:
                self.proxy_rotator.mark_success(proxy)
            
            self.logger.debug(f"Success: {url} (status={response.status_code})")
            return response
        
        except requests.exceptions.RequestException as e:
            if proxy:
                self.proxy_rotator.mark_failure(proxy)
            
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def fetch_multiple(self, urls: List[str], **kwargs) -> List[Dict]:
        """
        Fetch multiple URLs sequentially.
        
        Args:
            urls: List of URLs to fetch
            **kwargs: Additional arguments for each request
        
        Returns:
            List of dicts with {url, response, success}
        """
        results = []
        for url in urls:
            response = self.fetch(url, **kwargs)
            results.append({
                "url": url,
                "response": response,
                "success": response is not None
            })
        
        return results
    
    def get_proxy_stats(self) -> Dict:
        """Get statistics on proxy performance."""
        if not self.proxy_rotator:
            return {"error": "No proxies configured"}
        return self.proxy_rotator.get_stats()
    
    def close(self):
        """Clean up resources."""
        self.session.close()
        self.logger.info("Scraper closed")
