import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse

class WebScraperService:
    """
    A service to fetch and parse content from web pages.
    """
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
        self.ignore_paths = [
            "/contact-us", "/legal", "/privacy", "/careers", "/press",
            "/sitemap", "/events", "/partners", "/pricing", "/training",
            "/certification", "/support", "/account", "/blog", "/newsroom",
            "/forums", "/help", "/faqs", "/terms", "/cookies","/premiumsupport",
            "/podcast", "/about-aws", "/marketplace/seller-profile"
            # , "/accessibility", "/translate", "/podcasts" "/transcribe", "/management"
        ]

    async def fetch_page(self, url: str) -> str | None:
        """Fetches the HTML content of a given URL."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            print(f"⚠️  Skipping URL due to HTTP error: {e.response.status_code} for url {e.request.url}")
            return None
        except httpx.RequestError as e:
            print(f"❌ Error fetching {url}: {e}")
            return None
        
    def _normalize_url(self, url: str) -> str:
        """Strips query parameters and fragments from a URL."""
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    def parse_content(self, html: str, base_url: str) -> tuple[str, list[str]]:
        """
        Parses HTML to extract meaningful text content and relevant links.
        This parser is specifically tailored for the aws.amazon.com/architecture layout.
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Find the main content area of the page
        main_content = soup.find('main')
        if not main_content:
            return "", []

        # Extract text from relevant tags
        text_parts = []
        for element in main_content.find_all(['h1', 'h2', 'h3', 'p', 'li']):
            text_parts.append(element.get_text(separator=' ', strip=True))
        content_text = "\n".join(text_parts)

        # Search the entire body for links to maximize discovery
        body_content = soup.find('body')
        if not body_content:
            return content_text, []

        # Find all valid, relevant links to crawl next
        links = set()
        for a_tag in body_content.find_all('a', href=True):
            href = a_tag['href']

            if href.startswith(('mailto:', 'javascript:')):
                continue

            full_url = urljoin(base_url, href)
            normalized_url = self._normalize_url(full_url)
            parsed_url = urlparse(normalized_url)

            if (parsed_url.hostname == urlparse(base_url).hostname and
                not any(parsed_url.path.endswith(ext) for ext in ['.pdf', '.zip', '.jpg', '.png']) and
                not any(parsed_url.path.startswith(ignore) for ignore in self.ignore_paths)):
                links.add(normalized_url)
        
        return content_text, list(links)

# Global instance
web_scraper_service = WebScraperService()