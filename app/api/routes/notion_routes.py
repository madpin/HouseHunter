from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from pydantic import HttpUrl
from app.models.property import Property
from app.services.notion_service import NotionService
from app.services.property_service import PropertyService
from app.services.interest_points_service import InterestPointsService
from app.scrapers.scraper_factory import ScraperFactory

router = APIRouter(prefix="/notion", tags=["notion"])

# Dependency injection
def get_notion_service() -> NotionService:
    return NotionService()

def get_property_service() -> PropertyService:
    return PropertyService()

def get_scraper_factory() -> ScraperFactory:
    return ScraperFactory()
 
def get_interest_points_service() -> InterestPointsService:
    return InterestPointsService()

@router.post("/properties/save")
async def save_property_to_notion(
    property_id: str,
    notion_service: NotionService = Depends(get_notion_service),
    property_service: PropertyService = Depends(get_property_service),
    interest_points_service: InterestPointsService = Depends(get_interest_points_service)
):
    """
    Save an existing property to Notion database
    """
    try:
        # Get the property from our database
        property_obj = await property_service.get_property(property_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Compute predictions if property has coordinates, to enrich the Notion note
        prediction_info = None
        try:
            if (
                hasattr(property_obj, 'address') and 
                hasattr(property_obj.address, 'latitude') and 
                hasattr(property_obj.address, 'longitude') and
                property_obj.address.latitude is not None and 
                property_obj.address.longitude is not None
            ):
                property_address = f"{property_obj.address.city}, {property_obj.address.county or ''}"
                prediction_info = await interest_points_service.calculate_predictions_for_property(
                    property_obj.address.latitude,
                    property_obj.address.longitude,
                    property_address
                )
        except Exception:
            prediction_info = None
        
        # Save to Notion (pass predictions)
        result = await notion_service.save_property_to_notion(property_obj, prediction_info)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving property to Notion: {str(e)}")

@router.post("/properties/ingest-and-save")
async def ingest_and_save_to_notion(
    url: HttpUrl,
    notion_service: NotionService = Depends(get_notion_service),
    property_service: PropertyService = Depends(get_property_service),
    scraper_factory: ScraperFactory = Depends(get_scraper_factory),
    interest_points_service: InterestPointsService = Depends(get_interest_points_service)
):
    """
    Ingest a property from URL and save it to Notion database
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
        
        # Save to our database first
        saved_property = await property_service.create_property(property_data)
        
        # Compute predictions (if coordinates exist) before saving to Notion
        prediction_info = None
        try:
            if (
                hasattr(saved_property, 'address') and 
                hasattr(saved_property.address, 'latitude') and 
                hasattr(saved_property.address, 'longitude') and
                saved_property.address.latitude is not None and 
                saved_property.address.longitude is not None
            ):
                property_address = f"{saved_property.address.city}, {saved_property.address.county or ''}"
                prediction_info = await interest_points_service.calculate_predictions_for_property(
                    saved_property.address.latitude,
                    saved_property.address.longitude,
                    property_address
                )
        except Exception:
            prediction_info = None
        
        # Save to Notion with predictions
        notion_result = await notion_service.save_property_to_notion(saved_property, prediction_info)
        
        return {
            "property": saved_property,
            "notion_result": notion_result,
            "message": "Property ingested and saved to Notion successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting and saving property: {str(e)}")

@router.get("/database/info")
async def get_notion_database_info(
    notion_service: NotionService = Depends(get_notion_service)
):
    """
    Get information about the configured Notion database
    """
    try:
        info = await notion_service.get_database_info()
        
        if info["success"]:
            return info
        else:
            raise HTTPException(status_code=500, detail=info["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database info: {str(e)}")

@router.get("/database/check")
async def check_notion_database(
    notion_service: NotionService = Depends(get_notion_service)
):
    """
    Check if the Notion database is accessible
    """
    try:
        exists = await notion_service.check_database_exists()
        
        return {
            "database_accessible": exists,
            "message": "Database is accessible" if exists else "Database not accessible"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking database: {str(e)}")

@router.post("/properties/batch-save")
async def batch_save_properties_to_notion(
    property_ids: list[str],
    notion_service: NotionService = Depends(get_notion_service),
    property_service: PropertyService = Depends(get_property_service)
):
    """
    Save multiple properties to Notion database
    """
    try:
        results = []
        
        for property_id in property_ids:
            try:
                # Get the property
                property_obj = await property_service.get_property(property_id)
                if not property_obj:
                    results.append({
                        "property_id": property_id,
                        "success": False,
                        "error": "Property not found"
                    })
                    continue
                
                # Save to Notion
                result = await notion_service.save_property_to_notion(property_obj)
                results.append({
                    "property_id": property_id,
                    **result
                })
                
            except Exception as e:
                results.append({
                    "property_id": property_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Count successes and failures
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        return {
            "total_properties": len(property_ids),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch save: {str(e)}") 