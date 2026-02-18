from services.web_scraper_service import web_scraper_service
from services.vector_db_service import vector_db_service
from typing import Set
from dotenv import load_dotenv
import os

load_dotenv()
max_pages = int(os.getenv("MAX_PAGES"))

class DataIngestionService:
    """
    Orchestrates the process of scraping websites and ingesting content into the Vector DB.
    """
    def __init__(self, max_pages: int = max_pages):
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()

    async def ingest_website(self, start_url: str):
        """
        Crawls a website starting from a URL and ingests its content.
        """
        print(f"🚀 Starting data ingestion from: {start_url}")
        urls_to_visit = [start_url]
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            url = urls_to_visit.pop(0)
            if url in self.visited_urls:
                continue

            print(f"  -> Scraping: {url} ({len(self.visited_urls) + 1}/{self.max_pages})")
            self.visited_urls.add(url)

            html = await web_scraper_service.fetch_page(url)
            if not html:
                continue

            content, new_links = web_scraper_service.parse_content(html, url)
            
            if content:
                # Add the scraped content to the vector database
                # The 'description' is the content itself, which will be vectorized.
                vector_db_service.add_pattern(description=content, metadata={"source": url})
            
            for link in new_links:
                if link not in self.visited_urls:
                    urls_to_visit.append(link)
        
        print(f"✅ Data ingestion complete. Visited {len(self.visited_urls)} pages.")

# Global instance
data_ingestion_service = DataIngestionService()