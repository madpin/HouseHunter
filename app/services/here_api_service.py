import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from app.models.interest_points import TransportationMode, InterestPoint

logger = logging.getLogger(__name__)


class HereApiService:
    """Service for interacting with HERE API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://router.hereapi.com/v8"
        self.transit_url = "https://transit.router.hereapi.com/v8"
        
    def get_public_transit_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        departure_time: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get public transit route between two points using HERE Public Transit API v8
        
        Args:
            origin: Tuple of (latitude, longitude) for origin
            destination: Tuple of (latitude, longitude) for destination
            departure_time: Departure time in ISO 8601 format (e.g., "2023-12-01T09:00:00")
            
        Returns:
            Public transit route data or None if error
        """
        try:
            url = f"{self.transit_url}/routes"
            params = {
                "origin": f"{origin[0]},{origin[1]}",
                "destination": f"{destination[0]},{destination[1]}",
                "return": "travelSummary,polyline,actions",
                "alternatives": 1,
                "changes": 3,  # Maximum 3 transfers
                "pedestrian[maxDistance]": 2000,  # Max 2km walking
                "pedestrian[speed]": 1.4,  # Walking speed in m/s
                "apiKey": self.api_key
            }
            
            # Add departure time if provided
            if departure_time:
                params["departureTime"] = departure_time
            
            logger.info(f"Requesting public transit route from {origin} to {destination}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Public transit route request successful")
                return data
            else:
                logger.error(f"HERE Public Transit API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting public transit route: {e}")
            return None
    
    def get_route_summary(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float], 
        transport_mode: TransportationMode = TransportationMode.DRIVING
    ) -> Optional[Dict]:
        """
        Get route summary between two points
        
        Args:
            origin: Tuple of (latitude, longitude) for origin
            destination: Tuple of (latitude, longitude) for destination
            transport_mode: Transportation mode to use
            
        Returns:
            Route summary dict or None if error
        """
        try:
            # For public transport, use the dedicated transit API
            if transport_mode == TransportationMode.PUBLIC_TRANSPORT:
                return self.get_public_transit_route(origin, destination)
            
            # Convert transportation mode to HERE API format
            transport_mode_mapping = {
                TransportationMode.DRIVING: "car",
                TransportationMode.WALKING: "pedestrian", 
                TransportationMode.BICYCLING: "bicycle",
                TransportationMode.TRUCK: "truck",
                TransportationMode.TAXI: "taxi",
                TransportationMode.BUS: "bus",
                TransportationMode.TRAIN: "train",
                TransportationMode.SUBWAY: "subway",
                TransportationMode.TRAM: "tram",
                TransportationMode.FERRY: "ferry"
            }
            
            here_transport_mode = transport_mode_mapping.get(transport_mode, "car")
            
            url = f"{self.base_url}/routes"
            params = {
                "origin": f"{origin[0]},{origin[1]}",
                "destination": f"{destination[0]},{destination[1]}",
                "transportMode": here_transport_mode,
                "return": "summary,travelSummary",
                "apiKey": self.api_key
            }
            
            logger.info(f"Requesting route from {origin} to {destination} via {here_transport_mode}")
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Route request successful for {here_transport_mode}")
                return data
            else:
                logger.error(f"HERE API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting route summary: {e}")
            return None
            
    def get_matrix_routing(
        self,
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]], 
        transport_mode: TransportationMode = TransportationMode.DRIVING
    ) -> Optional[Dict]:
        """
        Get matrix routing between multiple origins and destinations
        
        Args:
            origins: List of (latitude, longitude) tuples for origins
            destinations: List of (latitude, longitude) tuples for destinations
            transport_mode: Transportation mode to use
            
        Returns:
            Matrix routing results or None if error
        """
        try:
            # Convert transportation mode to HERE API format
            transport_mode_mapping = {
                TransportationMode.DRIVING: "car",
                TransportationMode.WALKING: "pedestrian",
                TransportationMode.PUBLIC_TRANSPORT: "publicTransport", 
                TransportationMode.BICYCLING: "bicycle",
                TransportationMode.TRUCK: "truck",
                TransportationMode.TAXI: "taxi",
                TransportationMode.BUS: "bus",
                TransportationMode.TRAIN: "train",
                TransportationMode.SUBWAY: "subway",
                TransportationMode.TRAM: "tram",
                TransportationMode.FERRY: "ferry"
            }
            
            here_transport_mode = transport_mode_mapping.get(transport_mode, "car")
            
            # Format origins and destinations for HERE API
            origins_str = ";".join([f"{lat},{lng}" for lat, lng in origins])
            destinations_str = ";".join([f"{lat},{lng}" for lat, lng in destinations])
            
            url = f"{self.base_url}/matrix"
            params = {
                "origins": origins_str,
                "destinations": destinations_str,
                "transportMode": here_transport_mode,
                "return": "summary,travelSummary",
                "apiKey": self.api_key
            }
            
            # Add specific parameters for public transport
            if here_transport_mode == "bus":
                # For public transport, we need to specify departure time and routing preferences
                # Set departure time to next available time (current time + 5 minutes)
                departure_time = datetime.now() + timedelta(minutes=5)
                params["departureTime"] = departure_time.strftime("%Y-%m-%dT%H:%M:%S")
                params["routingMode"] = "fast"
                params["alternatives"] = 1
            
            logger.info(f"Requesting matrix routing for {len(origins)} origins to {len(destinations)} destinations via {here_transport_mode}")
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Matrix routing request successful for {here_transport_mode}")
                return data
            else:
                logger.error(f"HERE API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting matrix routing: {e}")
            return None

    async def calculate_prediction_time(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        transport_mode: Optional[TransportationMode] = None
    ) -> Optional[Dict]:
        """Calculate prediction time for next Friday at 9am between two points"""
        try:
            # Use default transport mode if none specified
            if transport_mode is None:
                transport_mode = TransportationMode.DRIVING
            
            # Calculate next Friday at 9am
            today = date.today()
            days_ahead = 4 - today.weekday()  # Friday is 4 (Monday is 0)
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_friday = today + timedelta(days=days_ahead)
            
            # Format departure time for API
            departure_time = f"{next_friday.isoformat()}T09:00:00"
            
            # Get route summary
            if transport_mode == TransportationMode.PUBLIC_TRANSPORT:
                route_data = self.get_public_transit_route(
                    (origin_lat, origin_lng),
                    (dest_lat, dest_lng),
                    departure_time
                )
            else:
                route_data = self.get_route_summary(
                    (origin_lat, origin_lng),
                    (dest_lat, dest_lng),
                    transport_mode
                )
            
            if route_data and "routes" in route_data and route_data["routes"]:
                route = route_data["routes"][0]
                
                # Handle public transport route structure
                if transport_mode == TransportationMode.PUBLIC_TRANSPORT:
                    return self._extract_public_transit_prediction(
                        route, origin_lat, origin_lng, dest_lat, dest_lng, 
                        transport_mode, next_friday, departure_time
                    )
                else:
                    # Handle regular route structure
                    return self._extract_regular_route_prediction(
                        route, origin_lat, origin_lng, dest_lat, dest_lng,
                        transport_mode, next_friday, departure_time
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating prediction time: {e}")
            return None
    
    def _extract_public_transit_prediction(
        self,
        route: Dict,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        transport_mode: TransportationMode,
        next_friday: date,
        departure_time: str
    ) -> Dict:
        """Extract prediction data from public transport route"""
        try:
            # Calculate total duration and distance from sections
            total_duration = 0
            total_distance = 0
            total_walking_duration = 0
            total_walking_distance = 0
            route_details = []
            
            if "sections" in route:
                for section in route["sections"]:
                    section_type = section.get("type", "unknown")
                    travel_summary = section.get("travelSummary", {})
                    section_duration = travel_summary.get("duration", 0)
                    section_length = travel_summary.get("length", 0)
                    
                    total_duration += section_duration
                    total_distance += section_length
                    
                    # Track walking sections separately
                    if section_type == "pedestrian":
                        total_walking_duration += section_duration
                        total_walking_distance += section_length
                    
                    # Extract section details
                    section_info = {
                        "type": section_type,
                        "duration_minutes": section_duration // 60,
                        "distance_m": section_length
                    }
                    
                    if section_type == "transit":
                        transport = section.get("transport", {})
                        section_info.update({
                            "mode": transport.get("mode", "unknown"),
                            "name": transport.get("name", "Unknown"),
                            "line": transport.get("line", "Unknown")
                        })
                    elif section_type == "pedestrian":
                        section_info.update({
                            "mode": "walking",
                            "name": "Walking"
                        })
                    
                    route_details.append(section_info)
            
            # Calculate arrival time
            departure_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            arrival_dt = departure_dt + timedelta(seconds=total_duration)
            
            return {
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "dest_lat": dest_lat,
                "dest_lng": dest_lng,
                "transport_mode": transport_mode.value,
                "distance_km": total_distance / 1000,
                "duration_minutes": total_duration // 60,
                "prediction_date": next_friday.isoformat(),
                "departure_time": "09:00",
                "arrival_time": arrival_dt.strftime("%H:%M"),
                "calculated_at": datetime.now().isoformat(),
                "route_details": route_details,
                "total_walking_minutes": total_walking_duration // 60,
                "total_walking_distance_km": total_walking_distance / 1000
            }
            
        except Exception as e:
            logger.error(f"Error extracting public transit prediction: {e}")
            return None
    
    def _extract_regular_route_prediction(
        self,
        route: Dict,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        transport_mode: TransportationMode,
        next_friday: date,
        departure_time: str
    ) -> Dict:
        """Extract prediction data from regular route"""
        try:
            summary = route.get("summary", {})
            duration_seconds = summary.get("duration", 0)
            
            # Calculate arrival time
            departure_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            arrival_dt = departure_dt + timedelta(seconds=duration_seconds)
            
            return {
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "dest_lat": dest_lat,
                "dest_lng": dest_lng,
                "transport_mode": transport_mode.value,
                "distance_km": summary.get("length", 0) / 1000,
                "duration_minutes": duration_seconds // 60,
                "prediction_date": next_friday.isoformat(),
                "departure_time": "09:00",
                "arrival_time": arrival_dt.strftime("%H:%M"),
                "calculated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting regular route prediction: {e}")
            return None

    async def batch_calculate_predictions(
        self,
        properties: List[Tuple[str, float, float]],
        interest_points: List[InterestPoint]
    ) -> List[Dict]:
        """Calculate predictions for multiple properties to all active interest points"""
        try:
            results = []
            
            for prop_id, prop_lat, prop_lng in properties:
                prop_predictions = []
                
                for point in interest_points:
                    try:
                        # Calculate prediction for this property-interest point pair
                        prediction = await self.calculate_prediction_time(
                            prop_lat, prop_lng,
                            point.latitude, point.longitude,
                            point.default_transportation_mode
                        )
                        
                        if prediction:
                            prediction["property_id"] = prop_id
                            prediction["interest_point_id"] = point.id
                            prediction["interest_point_name"] = point.name
                            prop_predictions.append(prediction)
                            
                    except Exception as e:
                        logger.error(f"Error calculating prediction for property {prop_id} to point {point.id}: {e}")
                        continue
                
                results.append({
                    "property_id": prop_id,
                    "predictions": prop_predictions,
                    "total_predictions": len(prop_predictions)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch prediction calculation: {e}")
            return [] 