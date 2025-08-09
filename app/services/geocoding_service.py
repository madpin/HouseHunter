import aiohttp
import logging
from typing import Optional, Tuple
from app.config import config

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for converting addresses to coordinates using HERE Geocoding API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.HERE_API_KEY
        self.base_url = "https://geocode.search.hereapi.com/v1/geocode"
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert an address to coordinates using HERE Geocoding API
        
        Args:
            address: The address to geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not self.api_key:
            logger.warning("HERE API key not configured for geocoding")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "apiKey": self.api_key,
                    "q": address,
                    "limit": 1
                }
                
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Geocoding API error: {response.status} - {await response.text()}")
                        return None
                    
                    data = await response.json()
                    
                    if "items" in data and data["items"]:
                        item = data["items"][0]
                        position = item.get("position", {})
                        lat = position.get("lat")
                        lng = position.get("lng")
                        
                        if lat is not None and lng is not None:
                            logger.info(f"Geocoded address '{address}' to coordinates: {lat}, {lng}")
                            return float(lat), float(lng)
                        else:
                            logger.warning(f"No coordinates found in geocoding response for address: {address}")
                    else:
                        logger.warning(f"No geocoding results found for address: {address}")
                        
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
        
        return None
    
    async def geocode_property_address(self, property_address) -> Optional[Tuple[float, float]]:
        """
        Geocode a property address object
        
        Args:
            property_address: Property address object with street, city, county, etc.
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not property_address:
            return None
        
        # Build a formatted address string
        address_parts = []
        
        if hasattr(property_address, 'street') and property_address.street:
            address_parts.append(property_address.street)
        
        if hasattr(property_address, 'city') and property_address.city:
            address_parts.append(property_address.city)
        
        if hasattr(property_address, 'county') and property_address.county:
            address_parts.append(property_address.county)
        
        if hasattr(property_address, 'postal_code') and property_address.postal_code:
            address_parts.append(property_address.postal_code)
        
        if hasattr(property_address, 'country') and property_address.country:
            address_parts.append(property_address.country)
        
        if not address_parts:
            logger.warning("No address parts available for geocoding")
            return None
        
        formatted_address = ", ".join(address_parts)
        logger.info(f"Attempting to geocode address: {formatted_address}")
        
        return await self.geocode_address(formatted_address)
