"""Proxy management and rotation utilities."""

import random
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Represents a single proxy."""
    url: str
    protocol: str = "http"  # http, https, socks5
    weight: float = 1.0  # for weighted rotation
    success_count: int = 0
    failure_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of this proxy."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def record_success(self):
        """Record a successful request through this proxy."""
        self.success_count += 1
    
    def record_failure(self):
        """Record a failed request through this proxy."""
        self.failure_count += 1


class ProxyRotator:
    """Manages proxy rotation and selection strategies."""
    
    def __init__(
        self,
        proxies: List[str],
        strategy: str = "round_robin",
        protocol: str = "http"
    ):
        """
        Initialize proxy rotator.
        
        Args:
            proxies: List of proxy URLs (e.g., ["http://proxy1.com:8080", ...])
            strategy: Rotation strategy - "round_robin", "random", or "weighted"
            protocol: Protocol for proxies - "http", "https", or "socks5"
        """
        self.proxies = [Proxy(url=p, protocol=protocol) for p in proxies]
        self.strategy = strategy
        self.current_index = 0
        
        if not self.proxies:
            raise ValueError("At least one proxy must be provided")
        
        logger.info(f"Initialized ProxyRotator with {len(self.proxies)} proxies ({strategy})")
    
    def get_next(self) -> Proxy:
        """Get the next proxy based on rotation strategy."""
        if self.strategy == "round_robin":
            return self._round_robin()
        elif self.strategy == "random":
            return self._random()
        elif self.strategy == "weighted":
            return self._weighted()
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _round_robin(self) -> Proxy:
        """Round-robin proxy selection."""
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def _random(self) -> Proxy:
        """Random proxy selection."""
        return random.choice(self.proxies)
    
    def _weighted(self) -> Proxy:
        """
        Weighted proxy selection based on success rates.
        Proxies with higher success rates are more likely to be selected.
        """
        total_weight = sum(p.weight * p.success_rate for p in self.proxies)
        if total_weight == 0:
            return random.choice(self.proxies)
        
        choice = random.uniform(0, total_weight)
        current = 0
        for proxy in self.proxies:
            current += proxy.weight * proxy.success_rate
            if choice <= current:
                return proxy
        
        return self.proxies[-1]
    
    def get_proxy_dict(self, proxy: Proxy) -> Dict[str, str]:
        """
        Get proxy dict formatted for requests library.
        
        Returns:
            {"http": "...", "https": "..."} or {"socks5": "..."}
        """
        if proxy.protocol == "socks5":
            return {"http": f"socks5://{proxy.url}", "https": f"socks5://{proxy.url}"}
        else:
            return {"http": proxy.url, "https": proxy.url}
    
    def mark_success(self, proxy: Proxy):
        """Mark a proxy as having successful request."""
        proxy.record_success()
        logger.debug(f"Proxy success recorded: {proxy.url} ({proxy.success_rate:.2%})")
    
    def mark_failure(self, proxy: Proxy):
        """Mark a proxy as having failed request."""
        proxy.record_failure()
        logger.warning(f"Proxy failure recorded: {proxy.url} ({proxy.success_rate:.2%})")
    
    def get_stats(self) -> Dict:
        """Get statistics on all proxies."""
        return {
            proxy.url: {
                "success_count": proxy.success_count,
                "failure_count": proxy.failure_count,
                "success_rate": proxy.success_rate,
            }
            for proxy in self.proxies
        }
