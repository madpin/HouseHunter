from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

class PropertyType(str, Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    DUPLEX = "duplex"
    TOWNHOUSE = "townhouse"
    BUNGALOW = "bungalow"
    COTTAGE = "cottage"
    PENTHOUSE = "penthouse"
    STUDIO = "studio"
    LAND = "land"
    COMMERCIAL = "commercial"

class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    RENTED = "rented"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

class WebsiteSource(str, Enum):
    DAFT = "daft"
    MYHOME = "myhome"
    DONDEAL = "dondeal"
    PROPERTYWEBSITE = "propertywebsite"
    RENT = "rent"
    OTHER = "other"

class Address(BaseModel):
    street: str
    city: str
    county: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Ireland"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None

class PropertyFeature(BaseModel):
    name: str
    value: Optional[str] = None
    category: Optional[str] = None

class PropertyImage(BaseModel):
    url: HttpUrl
    description: Optional[str] = None
    is_primary: bool = False
    order: Optional[int] = None

class AgentInfo(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    agency: Optional[str] = None
    website: Optional[HttpUrl] = None
    license_number: Optional[str] = None

class WebsiteListing(BaseModel):
    """Represents a property listing on a specific website"""
    website: WebsiteSource
    listing_id: str
    listing_url: HttpUrl
    price: float
    currency: str = "EUR"
    status: ListingStatus = ListingStatus.ACTIVE
    date_listed: Optional[date] = None
    date_updated: Optional[datetime] = None
    date_scraped: datetime = Field(default_factory=datetime.now)
    title: Optional[str] = None
    description: Optional[str] = None
    agent: Optional[AgentInfo] = None
    images: List[PropertyImage] = []
    features: List[PropertyFeature] = []
    raw_data: Optional[Dict[str, Any]] = None  # Store original scraped data

class Property(BaseModel):
    """Core property entity that can have multiple listings across websites"""
    id: Optional[str] = Field(None, description="Unique property identifier")
    
    # Core property information
    address: Address
    property_type: PropertyType
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqm: Optional[float] = None
    lot_size_sqm: Optional[float] = None
    year_built: Optional[int] = None
    
    # Energy and compliance
    energy_rating: Optional[str] = None
    ber_number: Optional[str] = None
    
    # Property characteristics
    is_new_build: Optional[bool] = None
    furnished: Optional[bool] = None
    parking: Optional[str] = None
    heating: Optional[str] = None
    views: Optional[List[str]] = None
    nearby_amenities: Optional[List[str]] = None
    
    # Multiple listings across websites
    listings: List[WebsiteListing] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Computed properties
    @property
    def active_listings(self) -> List[WebsiteListing]:
        """Get all active listings"""
        return [listing for listing in self.listings if listing.status == ListingStatus.ACTIVE]
    
    @property
    def primary_listing(self) -> Optional[WebsiteListing]:
        """Get the primary listing (first active one)"""
        active = self.active_listings
        return active[0] if active else None
    
    @property
    def min_price(self) -> Optional[float]:
        """Get minimum price across all active listings"""
        active = self.active_listings
        return min(listing.price for listing in active) if active else None
    
    @property
    def max_price(self) -> Optional[float]:
        """Get maximum price across all active listings"""
        active = self.active_listings
        return max(listing.price for listing in active) if active else None

class PropertySearchResult(BaseModel):
    """Result wrapper for property searches"""
    properties: List[Property]
    total_count: int
    page: int
    page_size: int
    filters_applied: Dict[str, Any] = {} 