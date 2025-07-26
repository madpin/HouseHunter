from typing import List, Optional, Dict, Any
from app.models.property import Property, WebsiteListing, WebsiteSource, ListingStatus
from datetime import datetime

class PropertyService:
    """Service layer for property-related business logic"""
    
    def __init__(self):
        # In a real implementation, this would connect to a database
        self.properties: Dict[str, Property] = {}
    
    async def create_property(self, property_data: Property) -> Property:
        """Create a new property"""
        if property_data.id is None:
            property_data.id = self._generate_property_id()
        
        property_data.created_at = datetime.now()
        property_data.updated_at = datetime.now()
        
        self.properties[property_data.id] = property_data
        return property_data
    
    async def get_property(self, property_id: str) -> Optional[Property]:
        """Get a property by ID"""
        return self.properties.get(property_id)
    
    async def update_property(self, property_id: str, property_data: Property) -> Optional[Property]:
        """Update an existing property"""
        if property_id not in self.properties:
            return None
        
        property_data.id = property_id
        property_data.updated_at = datetime.now()
        property_data.created_at = self.properties[property_id].created_at
        
        self.properties[property_id] = property_data
        return property_data
    
    async def add_listing(self, property_id: str, listing: WebsiteListing) -> Optional[Property]:
        """Add a new listing to an existing property"""
        property_obj = await self.get_property(property_id)
        if not property_obj:
            return None
        
        # Check if listing already exists
        existing_listing = next(
            (l for l in property_obj.listings 
             if l.website == listing.website and l.listing_id == listing.listing_id),
            None
        )
        
        if existing_listing:
            # Update existing listing
            existing_listing.price = listing.price
            existing_listing.status = listing.status
            existing_listing.date_updated = datetime.now()
            existing_listing.date_scraped = datetime.now()
            existing_listing.title = listing.title
            existing_listing.description = listing.description
            existing_listing.agent = listing.agent
            existing_listing.images = listing.images
            existing_listing.features = listing.features
            existing_listing.raw_data = listing.raw_data
        else:
            # Add new listing
            property_obj.listings.append(listing)
        
        property_obj.updated_at = datetime.now()
        return property_obj
    
    async def search_properties(self, filters: Dict[str, Any]) -> List[Property]:
        """Search properties based on filters"""
        results = list(self.properties.values())
        
        # Apply filters
        if 'city' in filters:
            results = [p for p in results if p.address.city.lower() == filters['city'].lower()]
        
        if 'property_type' in filters:
            results = [p for p in results if p.property_type == filters['property_type']]
        
        if 'min_price' in filters:
            results = [p for p in results if p.min_price and p.min_price >= filters['min_price']]
        
        if 'max_price' in filters:
            results = [p for p in results if p.max_price and p.max_price <= filters['max_price']]
        
        if 'bedrooms' in filters:
            results = [p for p in results if p.bedrooms and p.bedrooms >= filters['bedrooms']]
        
        if 'website' in filters:
            results = [p for p in results if any(l.website == filters['website'] for l in p.active_listings)]
        
        return results
    
    async def get_properties_by_website(self, website: WebsiteSource) -> List[Property]:
        """Get all properties that have listings on a specific website"""
        return [
            p for p in self.properties.values()
            if any(l.website == website for l in p.listings)
        ]
    
    async def update_listing_status(self, property_id: str, website: WebsiteSource, 
                                  listing_id: str, status: ListingStatus) -> Optional[Property]:
        """Update the status of a specific listing"""
        property_obj = await self.get_property(property_id)
        if not property_obj:
            return None
        
        for listing in property_obj.listings:
            if listing.website == website and listing.listing_id == listing_id:
                listing.status = status
                listing.date_updated = datetime.now()
                property_obj.updated_at = datetime.now()
                return property_obj
        
        return None
    
    def _generate_property_id(self) -> str:
        """Generate a unique property ID"""
        import uuid
        return str(uuid.uuid4()) 