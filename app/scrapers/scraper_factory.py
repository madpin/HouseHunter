from typing import List, Optional
from pydantic import HttpUrl
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.daft_scraper import DaftScraper
from app.models.property import Property

class ScraperFactory:
    """Factory for managing different website scrapers"""
    
    def __init__(self):
        self.scrapers: List[BaseScraper] = [
            DaftScraper(),
            # Add more scrapers here as they are implemented
            # MyHomeScraper(),
            # DonDealScraper(),
        ]
    
    def get_scraper_for_url(self, url: HttpUrl) -> Optional[BaseScraper]:
        """Get the appropriate scraper for a given URL"""
        for scraper in self.scrapers:
            if scraper.can_handle_url(url):
                return scraper
        return None
    
    async def scrape_property(self, url: HttpUrl) -> Optional[Property]:
        """Scrape a property using the appropriate scraper"""
        scraper = self.get_scraper_for_url(url)
        if not scraper:
            raise ValueError(f"No scraper available for URL: {url}")
        
        return await scraper.scrape_property(url)
    
    def get_supported_websites(self) -> List[str]:
        """Get list of supported website domains"""
        return [scraper.website.value for scraper in self.scrapers] 