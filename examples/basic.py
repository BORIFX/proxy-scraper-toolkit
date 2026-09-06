"""
Basic example: Scrape URLs with rate limiting and robots.txt compliance.
"""

from proxy_scraper_toolkit import Scraper, ScraperConfig

# Configure scraper with rate limiting
config = ScraperConfig(
    timeout=10,
    request_delay=1.0,  # 1 second between requests
    respect_robots_txt=True,  # Check robots.txt before fetching
    log_level="INFO"
)

scraper = Scraper(config)

# URLs to scrape
urls = [
    "https://example.com",
    "https://example.com/about",
    "https://example.com/contact",
]

print("Fetching URLs...\n")

# Fetch each URL
results = scraper.fetch_multiple(urls)

# Process results
for result in results:
    if result["success"]:
        response = result["response"]
        print(f"✓ {result['url']}")
        print(f"  Status: {response.status_code}")
        print(f"  Size: {len(response.text)} bytes\n")
    else:
        print(f"✗ {result['url']} - Failed to fetch\n")

scraper.close()
