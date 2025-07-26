from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import HttpUrl
from app.models.property import Property, PropertySearchResult, WebsiteSource
from app.services.property_service import PropertyService
from app.scrapers.scraper_factory import ScraperFactory

router = APIRouter(prefix="/properties", tags=["properties"])

# Dependency injection
def get_property_service() -> PropertyService:
    return PropertyService()

def get_scraper_factory() -> ScraperFactory:
    return ScraperFactory()

@router.post("/ingest", response_model=Property)
async def ingest_property_url(
    url: HttpUrl,
    property_service: PropertyService = Depends(get_property_service),
    scraper_factory: ScraperFactory = Depends(get_scraper_factory)
):
    """
    Ingest a property from a supported website URL
    """
    try:
        # Check if URL is supported
        scraper = scraper_factory.get_scraper_for_url(url)
        if not scraper:
            supported_sites = scraper_factory.get_supported_websites()
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported website. Supported sites: {', '.join(supported_sites)}"
            )
        
        # Scrape the property
        property_data = await scraper_factory.scrape_property(url)
        if not property_data:
            raise HTTPException(
                status_code=404,
                detail="Could not scrape property data from the provided URL"
            )
        
        # Save to database
        saved_property = await property_service.create_property(property_data)
        return saved_property
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting property: {str(e)}")

@router.get("/", response_model=PropertySearchResult)
async def search_properties(
    city: Optional[str] = Query(None, description="Filter by city"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    bedrooms: Optional[int] = Query(None, description="Minimum number of bedrooms"),
    website: Optional[str] = Query(None, description="Filter by website source"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    property_service: PropertyService = Depends(get_property_service)
):
    """
    Search properties with various filters
    """
    try:
        # Build filters
        filters = {}
        if city:
            filters['city'] = city
        if property_type:
            filters['property_type'] = property_type
        if min_price:
            filters['min_price'] = min_price
        if max_price:
            filters['max_price'] = max_price
        if bedrooms:
            filters['bedrooms'] = bedrooms
        if website:
            try:
                filters['website'] = WebsiteSource(website)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid website source. Valid options: {', '.join([ws.value for ws in WebsiteSource])}"
                )
        
        # Search properties
        all_properties = await property_service.search_properties(filters)
        
        # Apply pagination
        total_count = len(all_properties)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        properties = all_properties[start_idx:end_idx]
        
        return PropertySearchResult(
            properties=properties,
            total_count=total_count,
            page=page,
            page_size=page_size,
            filters_applied=filters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching properties: {str(e)}")

@router.get("/{property_id}", response_model=Property)
async def get_property(
    property_id: str,
    property_service: PropertyService = Depends(get_property_service)
):
    """
    Get a specific property by ID
    """
    property_obj = await property_service.get_property(property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return property_obj

@router.put("/{property_id}", response_model=Property)
async def update_property(
    property_id: str,
    property_data: Property,
    property_service: PropertyService = Depends(get_property_service)
):
    """
    Update a property
    """
    updated_property = await property_service.update_property(property_id, property_data)
    if not updated_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return updated_property

@router.get("/websites/supported")
async def get_supported_websites(
    scraper_factory: ScraperFactory = Depends(get_scraper_factory)
):
    """
    Get list of supported website sources
    """
    return {
        "supported_websites": scraper_factory.get_supported_websites(),
        "total_count": len(scraper_factory.get_supported_websites())
    }

@router.get("/websites/{website}/properties", response_model=List[Property])
async def get_properties_by_website(
    website: str,
    property_service: PropertyService = Depends(get_property_service)
):
    """
    Get all properties that have listings on a specific website
    """
    try:
        website_source = WebsiteSource(website)
        properties = await property_service.get_properties_by_website(website_source)
        return properties
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid website source. Valid options: {', '.join([ws.value for ws in WebsiteSource])}"
        )

@router.post("/scrape/daft", response_model=Property)
async def scrape_daft_property(
    url: HttpUrl,
    scraper_factory: ScraperFactory = Depends(get_scraper_factory)
):
    """
    Scrape a property from Daft.ie without saving to database
    """
    try:
        # Get the Daft scraper specifically
        scraper = scraper_factory.get_scraper_for_url(url)
        if not scraper or scraper.website != WebsiteSource.DAFT:
            raise HTTPException(
                status_code=400,
                detail="URL is not a valid Daft.ie property listing"
            )
        
        # Scrape the property
        property_data = await scraper.scrape_property(url)
        if not property_data:
            raise HTTPException(
                status_code=404,
                detail="Could not scrape property data from the provided URL"
            )
        
        return property_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping property: {str(e)}") 