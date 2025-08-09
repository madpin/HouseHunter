import logging
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import date, datetime
from app.models.interest_points import InterestPoint, TransportationMode, PropertyPredictionInfo, PredictionTimeResult
from app.services.here_api_service import HereApiService
from app.config import config

logger = logging.getLogger(__name__)


class InterestPointsService:
    """Service for managing interest points"""
    
    def __init__(self, config_file_path: str = "interest_points_config.json"):
        self.config_file_path = Path(config_file_path)
        self.interest_points: List[InterestPoint] = []
        self.here_service: Optional[HereApiService] = None
        self.load_interest_points()
    
    def load_interest_points(self) -> None:
        """Load interest points from configuration file"""
        try:
            if not self.config_file_path.exists():
                logger.warning(f"Configuration file {self.config_file_path} not found")
                return
            
            with open(self.config_file_path, 'r') as f:
                config_data = json.load(f)
            
            # Load interest points
            if "interest_points" in config_data:
                for point_data in config_data["interest_points"]:
                    try:
                        # Convert string transportation mode to enum
                        transport_mode_str = point_data.get("default_transportation_mode", "DRIVING")
                        transport_mode = TransportationMode(transport_mode_str)
                        
                        point = InterestPoint(
                            id=point_data["id"],
                            name=point_data["name"],
                            category=point_data.get("category", "general"),
                            latitude=point_data["latitude"],
                            longitude=point_data["longitude"],
                            address=point_data.get("address"),
                            description=point_data.get("description"),
                            rating=point_data.get("rating"),
                            opening_hours=point_data.get("opening_hours"),
                            phone=point_data.get("phone"),
                            website=point_data.get("website"),
                            price_level=point_data.get("price_level"),
                            photos=point_data.get("photos", []),
                            tags=point_data.get("tags", []),
                            created_at=point_data.get("created_at"),
                            updated_at=point_data.get("updated_at"),
                            is_active=point_data.get("is_active", True),
                            source=point_data.get("source"),
                            external_id=point_data.get("external_id"),
                            metadata=point_data.get("metadata", {}),
                            default_transportation_mode=transport_mode
                        )
                        self.interest_points.append(point)
                        
                    except Exception as e:
                        logger.error(f"Error loading interest point {point_data.get('id', 'unknown')}: {e}")
                        continue
            
            logger.info(f"Loaded {len(self.interest_points)} interest points")
            
        except Exception as e:
            logger.error(f"Error loading interest points configuration: {e}")
    
    def get_all_interest_points(self) -> List[InterestPoint]:
        """Get all interest points"""
        return self.interest_points
    
    def get_active_interest_points(self) -> List[InterestPoint]:
        """Get only active interest points"""
        return [point for point in self.interest_points if point.is_active]
    
    def get_interest_point_by_id(self, point_id: str) -> Optional[InterestPoint]:
        """Get interest point by ID"""
        for point in self.interest_points:
            if point.id == point_id:
                return point
        return None
    
    def get_interest_points_by_category(self, category: str) -> List[InterestPoint]:
        """Get interest points by category"""
        return [point for point in self.interest_points if point.category == category]
    
    def add_interest_point(self, point: InterestPoint) -> bool:
        """Add a new interest point"""
        try:
            # Check if point with same ID already exists
            if self.get_interest_point_by_id(point.id):
                logger.warning(f"Interest point with ID {point.id} already exists")
                return False
            
            self.interest_points.append(point)
            logger.info(f"Added interest point: {point.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding interest point: {e}")
            return False
    
    def update_interest_point(self, point_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing interest point"""
        try:
            point = self.get_interest_point_by_id(point_id)
            if not point:
                logger.warning(f"Interest point with ID {point_id} not found")
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(point, field):
                    setattr(point, field, value)
            
            logger.info(f"Updated interest point: {point.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating interest point: {e}")
            return False
    
    def delete_interest_point(self, point_id: str) -> bool:
        """Delete an interest point"""
        try:
            point = self.get_interest_point_by_id(point_id)
            if not point:
                logger.warning(f"Interest point with ID {point_id} not found")
                return False
            
            self.interest_points.remove(point)
            logger.info(f"Deleted interest point: {point.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting interest point: {e}")
            return False
    
    def save_configuration(self) -> bool:
        """Save current configuration to file"""
        try:
            config_data = {
                "settings": {
                    "default_transportation_mode": "DRIVING",
                    "default_departure_time": "09:00",
                    "default_departure_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "interest_points": []
            }
            
            for point in self.interest_points:
                point_data = {
                    "id": point.id,
                    "name": point.name,
                    "category": point.category,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "address": point.address,
                    "description": point.description,
                    "rating": point.rating,
                    "opening_hours": point.opening_hours,
                    "phone": point.phone,
                    "website": point.website,
                    "price_level": point.price_level,
                    "photos": point.photos,
                    "tags": point.tags,
                    "created_at": point.created_at,
                    "updated_at": point.updated_at,
                    "is_active": point.is_active,
                    "source": point.source,
                    "external_id": point.external_id,
                    "metadata": point.metadata,
                    "default_transportation_mode": point.default_transportation_mode.value
                }
                config_data["interest_points"].append(point_data)
            
            with open(self.config_file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get_here_service(self) -> HereApiService:
        """Get or create a HERE API service instance"""
        if self.here_service is None:
            if not config.validate_here_api_config():
                raise ValueError("HERE API configuration incomplete. Set HERE_API_KEY and HERE_API_ENABLED=true environment variables.")
            self.here_service = HereApiService(config.HERE_API_KEY)
        return self.here_service
    
    async def calculate_predictions_for_property(
        self, 
        latitude: float, 
        longitude: float, 
        property_address: str
    ) -> PropertyPredictionInfo:
        """Calculate prediction times for next Friday at 9am from a property to all active interest points"""
        try:
            # Get next Friday at 9am
            next_friday = self._get_next_friday_9am()
            
            # Get active interest points
            active_points = self.get_active_interest_points()
            if not active_points:
                logger.warning("No active interest points found")
                return PropertyPredictionInfo(
                    property_id="property",
                    property_address=property_address,
                    property_latitude=latitude,
                    property_longitude=longitude,
                    prediction_date=next_friday,
                    predictions=[]
                )
            
            # Get HERE service
            here_service = self.get_here_service()
            
            # Calculate predictions for each interest point
            predictions = []
            for point in active_points:
                try:
                    # Use the point's default transportation mode
                    transport_mode = point.default_transportation_mode
                    
                    # Calculate prediction time using the updated HERE API service
                    prediction_data = await here_service.calculate_prediction_time(
                        latitude, longitude,
                        point.latitude, point.longitude,
                        transport_mode
                    )
                    
                    if prediction_data:
                        # Create prediction result from the API response
                        prediction = PredictionTimeResult(
                            origin_point_id="property",
                            destination_point_id=point.id,
                            transportation_mode=transport_mode,
                            distance_km=prediction_data.get("distance_km", 0),
                            duration_minutes=prediction_data.get("duration_minutes", 0),
                            prediction_date=next_friday,
                            departure_time=prediction_data.get("departure_time", "09:00"),
                            arrival_time=prediction_data.get("arrival_time", "09:00"),
                            route_summary=f"Route to {point.name}",
                            route_details=prediction_data.get("route_details"),
                            total_walking_minutes=prediction_data.get("total_walking_minutes"),
                            total_walking_distance_km=prediction_data.get("total_walking_distance_km"),
                            calculated_at=datetime.now()
                        )
                        predictions.append(prediction)
                        
                except Exception as e:
                    logger.error(f"Error calculating prediction for point {point.id}: {e}")
                    continue
            
            # Create and return prediction info
            prediction_info = PropertyPredictionInfo(
                property_id="property",
                property_address=property_address,
                property_latitude=latitude,
                property_longitude=longitude,
                prediction_date=next_friday,
                predictions=predictions,
                calculated_at=datetime.now()
            )
            
            logger.info(f"Calculated {len(predictions)} predictions for property at {latitude}, {longitude}")
            return prediction_info
            
        except Exception as e:
            logger.error(f"Error calculating predictions for property: {e}")
            return PropertyPredictionInfo(
                property_id="property",
                property_address=property_address,
                property_latitude=latitude,
                property_longitude=longitude,
                prediction_date=self._get_next_friday_9am(),
                predictions=[],
                calculated_at=datetime.now()
            )

    def _get_next_friday_9am(self) -> date:
        """Get the next Friday at 9am date"""
        from datetime import timedelta
        
        today = date.today()
        days_ahead = 4 - today.weekday()  # Friday is 4 (Monday is 0)
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_friday = today + timedelta(days=days_ahead)
        return next_friday

    def _calculate_arrival_time(self, duration_seconds: int) -> str:
        """Calculate arrival time based on departure time (9am) and duration"""
        from datetime import datetime, timedelta
        
        departure_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        arrival_time = departure_time + timedelta(seconds=duration_seconds)
        return arrival_time.strftime("%H:%M")

    async def close(self):
        """Clean up resources"""
        # This method is called by test scripts but doesn't need cleanup
        pass 