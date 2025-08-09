from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from app.models.interest_points import (
    InterestPoint, TransportationMode, DistanceResult, PropertyDistanceInfo,
    PredictionTimeResult, PropertyPredictionInfo
)
from app.services.interest_points_service import InterestPointsService
from app.models.property import Property
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interest-points", tags=["Interest Points"])

# Global service instance
interest_points_service = InterestPointsService("config/interest_points_config.json")

@router.get("/", response_model=List[InterestPoint])
async def get_all_interest_points(active_only: bool = False):
    """Get all interest points"""
    try:
        if active_only:
            return interest_points_service.get_active_interest_points()
        return interest_points_service.get_all_interest_points()
    except Exception as e:
        logger.error(f"Error getting interest points: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{point_id}", response_model=InterestPoint)
async def get_interest_point(point_id: str):
    """Get a specific interest point by ID"""
    try:
        point = interest_points_service.get_interest_point_by_id(point_id)
        if not point:
            raise HTTPException(status_code=404, detail="Interest point not found")
        return point
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interest point {point_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/category/{category}", response_model=List[InterestPoint])
async def get_interest_points_by_category(category: str):
    """Get interest points by category"""
    try:
        points = interest_points_service.get_interest_points_by_category(category)
        return points
    except Exception as e:
        logger.error(f"Error getting interest points by category {category}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=InterestPoint)
async def create_interest_point(point: InterestPoint):
    """Create a new interest point"""
    try:
        success = interest_points_service.add_interest_point(point)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create interest point")
        return point
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating interest point: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{point_id}", response_model=InterestPoint)
async def update_interest_point(point_id: str, updates: Dict[str, Any]):
    """Update an existing interest point"""
    try:
        success = interest_points_service.update_interest_point(point_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Interest point not found")
        
        # Return the updated point
        updated_point = interest_points_service.get_interest_point_by_id(point_id)
        return updated_point
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating interest point {point_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{point_id}")
async def delete_interest_point(point_id: str):
    """Delete an interest point"""
    try:
        success = interest_points_service.delete_interest_point(point_id)
        if not success:
            raise HTTPException(status_code=404, detail="Interest point not found")
        return {"message": "Interest point deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting interest point {point_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/{point_id}/toggle")
async def toggle_interest_point(point_id: str):
    """Toggle the active status of an interest point"""
    try:
        success = interest_points_service.toggle_interest_point(point_id)
        if not success:
            raise HTTPException(status_code=404, detail="Interest point not found")
        
        point = interest_points_service.get_interest_point_by_id(point_id)
        return {
            "message": f"Interest point '{point.name}' toggled to {'active' if point.is_active else 'inactive'}",
            "point": point
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling interest point {point_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/calculate-distance")
async def calculate_distance(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    transport_mode: Optional[TransportationMode] = None
):
    """Calculate distance between two points"""
    try:
        here_service = interest_points_service.get_here_service()
        result = await here_service.calculate_distance(
            origin_lat, origin_lng, dest_lat, dest_lng, transport_mode
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Could not calculate distance")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/calculate-property-distances")
async def calculate_property_distances(
    property_lat: float,
    property_lng: float,
    property_address: str = "Property Location"
):
    """Calculate distances from a property to all active interest points"""
    try:
        here_service = interest_points_service.get_here_service()
        active_points = interest_points_service.get_active_interest_points()
        
        if not active_points:
            raise HTTPException(status_code=400, detail="No active interest points found")
        
        result = await here_service.calculate_distances_to_interest_points(
            property_lat, property_lng, active_points
        )
        
        # Update property address
        result.property_address = property_address
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating property distances: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/batch-calculate-distances")
async def batch_calculate_distances(
    properties: List[Dict[str, Any]]
):
    """Calculate distances for multiple properties to all active interest points"""
    try:
        here_service = interest_points_service.get_here_service()
        active_points = interest_points_service.get_active_interest_points()
        
        if not active_points:
            raise HTTPException(status_code=400, detail="No active interest points found")
        
        # Prepare property data
        property_data = []
        for prop in properties:
            if "id" not in prop or "latitude" not in prop or "longitude" not in prop:
                raise HTTPException(status_code=400, detail="Invalid property data format")
            property_data.append((prop["id"], prop["latitude"], prop["longitude"]))
        
        results = await here_service.batch_calculate_distances(property_data, active_points)
        
        return {
            "results": results,
            "total_properties": len(results),
            "total_interest_points": len(active_points)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch distance calculation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/export-config")
async def export_config(file_path: str):
    """Export current interest points configuration"""
    try:
        success = interest_points_service.export_config(file_path)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to export configuration")
        return {"message": f"Configuration exported to {file_path}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/import-config")
async def import_config(file_path: str):
    """Import interest points configuration from file"""
    try:
        success = interest_points_service.import_config(file_path)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to import configuration")
        return {"message": f"Configuration imported from {file_path}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/clear-cache")
async def clear_cache():
    """Clear the distance calculation cache"""
    try:
        here_service = interest_points_service.get_here_service()
        here_service.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/calculate-prediction")
async def calculate_prediction(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    transport_mode: Optional[TransportationMode] = None
):
    """Calculate prediction time for next Friday at 9am between two points"""
    try:
        here_service = interest_points_service.get_here_service()
        result = await here_service.calculate_prediction_time(
            origin_lat, origin_lng, dest_lat, dest_lng, transport_mode
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Could not calculate prediction")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/calculate-property-predictions", response_model=PropertyPredictionInfo)
async def calculate_property_predictions(
    property_lat: float,
    property_lng: float,
    property_address: str = "Property Location"
):
    """Calculate prediction times for next Friday at 9am from a property to all active interest points"""
    try:
        result = await interest_points_service.calculate_predictions_for_property(
            property_lat, property_lng, property_address
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Could not calculate predictions")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating property predictions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/batch-calculate-predictions")
async def batch_calculate_predictions(
    properties: List[Dict[str, Any]]
):
    """Calculate predictions for multiple properties to all active interest points for next Friday at 9am"""
    try:
        here_service = interest_points_service.get_here_service()
        active_points = interest_points_service.get_active_interest_points()
        
        if not active_points:
            raise HTTPException(status_code=400, detail="No active interest points found")
        
        # Prepare property data
        property_data = []
        for prop in properties:
            if "id" not in prop or "latitude" not in prop or "longitude" not in prop:
                raise HTTPException(status_code=400, detail="Invalid property data format")
            property_data.append((prop["id"], prop["latitude"], prop["longitude"]))
        
        results = await here_service.batch_calculate_predictions(property_data, active_points)
        
        return {
            "results": results,
            "total_properties": len(results),
            "total_interest_points": len(active_points)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch prediction calculation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 