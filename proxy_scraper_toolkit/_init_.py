"""
proxy-scraper-toolkit: A lightweight toolkit for building resilient web scrapers.

Provides proxy rotation, rate limiting, retries, robots.txt checking, and structured
logging for developers who need to scale scraping workflows responsibly.
"""

from .scraper import Scraper
from .proxy import ProxyRotator
from .config import ScraperConfig

__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = ["Scraper", "ProxyRotator", "ScraperConfig"]
