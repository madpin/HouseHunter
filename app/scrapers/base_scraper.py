from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.property import Property, WebsiteListing, WebsiteSource
from pydantic import HttpUrl

class BaseScraper(ABC):
    """Base class for all website scrapers"""
    
    def __init__(self, website: WebsiteSource):
        self.website = website
    
    @abstractmethod
    async def scrape_property(self, url: HttpUrl) -> Optional[Property]:
        """
        Scrape a property from a given URL
        
        Args:
            url: The URL of the property listing
            
        Returns:
            Property object with scraped data, or None if scraping failed
        """
        pass
    
    @abstractmethod
    def can_handle_url(self, url: HttpUrl) -> bool:
        """
        Check if this scraper can handle the given URL
        
        Args:
            url: The URL to check
            
        Returns:
            True if this scraper can handle the URL, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_listing_id(self, url: HttpUrl) -> Optional[str]:
        """
        Extract the listing ID from a URL
        
        Args:
            url: The URL to extract the listing ID from
            
        Returns:
            The listing ID, or None if it cannot be extracted
        """
        pass
    
    def create_website_listing(self, url: HttpUrl, price: float, 
                             title: Optional[str] = None,
                             description: Optional[str] = None,
                             raw_data: Optional[Dict[str, Any]] = None) -> WebsiteListing:
        """
        Create a WebsiteListing object with common fields
        
        Args:
            url: The listing URL
            price: The property price
            title: The listing title
            description: The listing description
            raw_data: Raw scraped data
            
        Returns:
            WebsiteListing object
        """
        listing_id = self.extract_listing_id(url)
        if not listing_id:
            raise ValueError(f"Could not extract listing ID from URL: {url}")
        
        return WebsiteListing(
            website=self.website,
            listing_id=listing_id,
            listing_url=url,
            price=price,
            title=title,
            description=description,
            raw_data=raw_data
        ) 