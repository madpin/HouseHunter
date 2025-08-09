from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, date, timedelta


class TransportationMode(str, Enum):
    """Transportation modes supported by HERE API"""
    DRIVING = "car"
    WALKING = "pedestrian"
    PUBLIC_TRANSPORT = "publicTransport"
    BICYCLING = "bicycle"
    TRUCK = "truck"
    TAXI = "taxi"
    BUS = "bus"
    TRAIN = "train"
    SUBWAY = "subway"
    TRAM = "tram"
    FERRY = "ferry"


class InterestPoint(BaseModel):
    """Model for interest points"""
    id: str = Field(..., description="Unique identifier for the interest point")
    name: str = Field(..., description="Name of the interest point")
    category: str = Field(..., description="Category of the interest point")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Address of the interest point")
    description: Optional[str] = Field(None, description="Description of the interest point")
    rating: Optional[float] = Field(None, description="Rating of the interest point")
    opening_hours: Optional[str] = Field(None, description="Opening hours of the interest point")
    phone: Optional[str] = Field(None, description="Phone number of the interest point")
    website: Optional[str] = Field(None, description="Website of the interest point")
    price_level: Optional[str] = Field(None, description="Price level of the interest point")
    photos: Optional[List[str]] = Field(None, description="List of photo URLs")
    tags: Optional[List[str]] = Field(None, description="List of tags for the interest point")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    is_active: bool = Field(True, description="Whether the interest point is active")
    source: Optional[str] = Field(None, description="Source of the interest point data")
    external_id: Optional[str] = Field(None, description="External ID from the source system")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    default_transportation_mode: TransportationMode = TransportationMode.DRIVING


class DistanceResult(BaseModel):
    """Result of distance calculation between two points"""
    origin_point_id: str
    destination_point_id: str
    transportation_mode: TransportationMode
    distance_km: float
    duration_minutes: int
    route_summary: Optional[str] = None
    traffic_info: Optional[Dict[str, Any]] = None
    calculated_at: datetime = Field(default_factory=datetime.now)

class PredictionTimeResult(BaseModel):
    """Result of prediction time calculation for next Friday"""
    origin_point_id: str
    destination_point_id: str
    transportation_mode: TransportationMode
    distance_km: float
    duration_minutes: int
    prediction_date: date = Field(..., description="Date of prediction (next Friday)")
    departure_time: Optional[str] = Field(None, description="Departure time for the prediction")
    arrival_time: Optional[str] = Field(None, description="Arrival time for the prediction")
    route_summary: Optional[str] = None
    route_details: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed route information including sections with type, duration, mode, etc.")
    traffic_info: Optional[Dict[str, Any]] = None
    total_walking_minutes: Optional[int] = Field(None, description="Total walking time in minutes")
    total_walking_distance_km: Optional[float] = Field(None, description="Total walking distance in kilometers")
    calculated_at: datetime = Field(default_factory=datetime.now)

class PropertyDistanceInfo(BaseModel):
    """Distance information for a property to all interest points"""
    property_id: str
    property_address: str
    property_latitude: float
    property_longitude: float
    distances: List[DistanceResult] = []
    calculated_at: datetime = Field(default_factory=datetime.now)
    
    def get_distance_to_point(self, point_id: str) -> Optional[DistanceResult]:
        """Get distance to a specific interest point"""
        for distance in self.distances:
            if distance.destination_point_id == point_id:
                return distance
        return None
    
    def get_closest_point(self) -> Optional[DistanceResult]:
        """Get the closest interest point by duration"""
        if not self.distances:
            return None
        return min(self.distances, key=lambda x: x.duration_minutes)
    
    def get_farthest_point(self) -> Optional[DistanceResult]:
        """Get the farthest interest point by duration"""
        if not self.distances:
            return None
        return max(self.distances, key=lambda x: x.duration_minutes)

class PropertyPredictionInfo(BaseModel):
    """Prediction time information for a property to all interest points for next Friday"""
    property_id: str
    property_address: str
    property_latitude: float
    property_longitude: float
    prediction_date: date = Field(..., description="Date of prediction (next Friday)")
    predictions: List[PredictionTimeResult] = []
    calculated_at: datetime = Field(default_factory=datetime.now)
    
    def get_prediction_to_point(self, point_id: str) -> Optional[PredictionTimeResult]:
        """Get prediction to a specific interest point"""
        for prediction in self.predictions:
            if prediction.destination_point_id == point_id:
                return prediction
        return None
    
    def get_fastest_prediction(self) -> Optional[PredictionTimeResult]:
        """Get the fastest prediction by duration"""
        if not self.predictions:
            return None
        return min(self.predictions, key=lambda x: x.duration_minutes)
    
    def get_slowest_prediction(self) -> Optional[PredictionTimeResult]:
        """Get the slowest prediction by duration"""
        if not self.predictions:
            return None
        return max(self.predictions, key=lambda x: x.duration_minutes)

class InterestPointsConfig(BaseModel):
    """Configuration for interest points system"""
    here_api_key: str
    default_transportation_mode: TransportationMode = TransportationMode.DRIVING
    cache_duration_hours: int = 24
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30
    enable_traffic_info: bool = True
    enable_route_details: bool = False 