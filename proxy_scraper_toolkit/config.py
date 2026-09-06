"""Configuration and settings for the scraper toolkit."""

from dataclasses import dataclass
from typing import Optional, List
import logging


@dataclass
class ScraperConfig:
    """Configuration for scraper behavior."""
    
    # Request settings
    timeout: int = 10
    max_retries: int = 3
    retry_backoff: float = 1.5  # multiplier for exponential backoff
    
    # Rate limiting
    request_delay: float = 1.0  # seconds between requests
    concurrent_requests: int = 1
    
    # Proxy settings
    use_proxies: bool = False
    proxy_rotation_strategy: str = "round_robin"  # round_robin, random, weighted
    
    # Request headers
    user_agent: Optional[str] = None
    custom_headers: dict = None
    
    # Robots.txt
    respect_robots_txt: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.custom_headers is None:
            self.custom_headers = {}
        
        if self.request_delay < 0:
            raise ValueError("request_delay must be non-negative")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        
        valid_strategies = ["round_robin", "random", "weighted"]
        if self.proxy_rotation_strategy not in valid_strategies:
            raise ValueError(f"proxy_rotation_strategy must be one of {valid_strategies}")


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging for the scraper."""
    logger = logging.getLogger("proxy_scraper_toolkit")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
