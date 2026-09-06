"""
Proxy rotation example: Cycle through proxies with performance tracking.
"""

from proxy_scraper_toolkit import Scraper, ScraperConfig

# Configure scraper with proxy rotation
config = ScraperConfig(
    timeout=10,
    request_delay=0.5,
    use_proxies=True,
    proxy_rotation_strategy="weighted",  # Prefer working proxies
    log_level="INFO"
)

scraper = Scraper(config)

# Set up proxies (replace with real proxy URLs)
proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080",
]

scraper.set_proxies(proxies, strategy="weighted")

# Target URL
url = "https://httpbin.org/ip"  # Returns your current IP

print("Testing proxy rotation...\n")

# Make 10 requests, cycling through proxies
for i in range(10):
    response = scraper.fetch(url)
    if response:
        print(f"Request {i+1}: {response.json()}\n")
    else:
        print(f"Request {i+1}: Failed\n")

# Print proxy statistics
print("Proxy Performance Stats:")
print("-" * 60)
stats = scraper.get_proxy_stats()
for proxy_url, proxy_stats in stats.items():
    success_rate = proxy_stats["success_rate"]
    print(f"{proxy_url}")
    print(f"  Success: {proxy_stats['success_count']}")
    print(f"  Failures: {proxy_stats['failure_count']}")
    print(f"  Success Rate: {success_rate:.1%}\n")

scraper.close()
