# Prediction Times Implementation

## Overview
This document outlines the implementation of prediction times functionality for the HouseHunter application. The system calculates travel times between properties and interest points using different transportation modes.

## Features
- **Multi-modal Transportation**: Support for driving, walking, public transport, and cycling
- **Real-time Calculations**: Uses HERE API for accurate travel time estimates
- **Caching System**: Intelligent caching to reduce API calls and improve performance
- **Batch Processing**: Efficient handling of multiple property-interest point combinations
- **Traffic Integration**: Real-time traffic data for driving routes

## Transportation Modes

The system supports the following transportation modes:

### 1. Driving (DRIVING)
- **Value**: `DRIVING`
- **Description**: Car travel with traffic consideration
- **Best for**: Commuting, shopping trips, time-sensitive travel
- **Traffic**: Real-time traffic data included

### 2. Walking (WALKING)
- **Value**: `WALKING`
- **Description**: Pedestrian routes
- **Best for**: Short distances, exercise, exploring neighborhoods
- **Features**: Sidewalk and pedestrian path routing

### 3. Public Transport (PUBLIC_TRANSPORT)
- **Value**: `PUBLIC_TRANSPORT`
- **Description**: Public transportation (bus, train, etc.)
- **Best for**: Commuting, long-distance travel, cost-effective travel
- **Features**: Multi-modal routing, schedules, transfers

### 4. Cycling (BICYCLING)
- **Value**: `BICYCLING`
- **Description**: Bicycle routes
- **Best for**: Exercise, eco-friendly travel, avoiding traffic
- **Features**: Bike lane routing, elevation consideration

## API Endpoints

### 1. Calculate Property Distances
```
POST /interest-points/calculate-property-distances
```

**Request Body:**
```json
{
  "property_lat": 53.3498,
  "property_lng": -6.2603,
  "property_address": "123 Main Street, Dublin"
}
```

**Response:**
```json
{
  "property_id": "property",
  "property_address": "123 Main Street, Dublin",
  "property_latitude": 53.3498,
  "property_longitude": -6.2603,
  "distances": [
    {
      "origin_point_id": "property",
      "destination_point_id": "work_location",
      "transportation_mode": "DRIVING",
      "distance_km": 2.5,
      "duration_minutes": 8,
      "route_summary": "Route via 3 sections",
      "traffic_info": {
        "traffic_delay": 0,
        "traffic_length": 0
      },
      "calculated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "calculated_at": "2024-01-01T12:00:00Z"
}
```

### 2. Batch Distance Calculation
```
POST /interest-points/batch-calculate-distances
```

**Request Body:**
```json
[
  {
    "id": "property_1",
    "latitude": 53.3498,
    "longitude": -6.2603
  },
  {
    "id": "property_2",
    "latitude": 53.3500,
    "longitude": -6.2600
  }
]
```

### 3. Direct Distance Calculation
```
POST /interest-points/calculate-distance
```

**Query Parameters:**
- `origin_lat`: Origin latitude
- `origin_lng`: Origin longitude
- `dest_lat`: Destination latitude
- `dest_lng`: Destination longitude
- `transport_mode`: Transportation mode (DRIVING, WALKING, PUBLIC_TRANSPORT, BICYCLING)

## Implementation Details

### 1. HERE API Integration
The system uses HERE Maps API v8 for routing calculations:

```python
class HereApiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://router.hereapi.com/v8"
    
    def get_route_summary(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float], 
        transport_mode: TransportationMode = TransportationMode.DRIVING
    ) -> Optional[Dict]:
        # Implementation details...
```

### 2. Transportation Mode Mapping
Transportation modes are mapped to HERE API values:

```python
TRANSPORT_MODE_MAPPING = {
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
```

### 3. Caching System
The system implements intelligent caching to reduce API calls:

```python
class DistanceCache:
    def __init__(self, cache_duration_hours: int = 24):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache = {}
    
    def get_cached_distance(self, key: str) -> Optional[Dict]:
        # Cache implementation...
    
    def cache_distance(self, key: str, distance_data: Dict) -> None:
        # Cache storage...
```

### 4. Error Handling
Comprehensive error handling for API failures:

```python
try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()
except requests.exceptions.RequestException as e:
    logger.error(f"HERE API error: {e}")
    return None
```

## Configuration

### Environment Variables
```bash
# HERE API Configuration
HERE_API_KEY=your_here_api_key_here
HERE_API_ENABLED=true
```

### Interest Points Configuration
```json
{
  "interest_points": [
    {
      "id": "work_location",
      "name": "My Work",
      "transportation_mode": "DRIVING",
      "latitude": 53.3498,
      "longitude": -6.2603
    }
  ],
  "settings": {
    "default_transportation_mode": "DRIVING",
    "cache_duration_hours": 24,
    "max_concurrent_requests": 10
  }
}
```

## Performance Considerations

### 1. Caching Strategy
- **Cache Duration**: 24 hours by default
- **Cache Key**: Includes coordinates, transportation mode, and timestamp
- **Cache Invalidation**: Automatic expiration and manual clearing

### 2. Rate Limiting
- **Concurrent Requests**: Maximum 10 concurrent API calls
- **Request Timeout**: 30 seconds per request
- **Retry Logic**: Exponential backoff for failed requests

### 3. Batch Processing
- **Efficient Grouping**: Process multiple properties together
- **Parallel Execution**: Concurrent API calls where possible
- **Memory Management**: Stream processing for large datasets

## Testing

### Unit Tests
```bash
python -m pytest tests/test_prediction_times.py -v
```

### Integration Tests
```bash
python -m pytest tests/test_here_api_service.py -v
```

### Manual Testing
```bash
python test_prediction_times.py
```

## Monitoring and Logging

### Log Levels
- **DEBUG**: Detailed API request/response information
- **INFO**: General operation information
- **WARNING**: Non-critical issues
- **ERROR**: API failures and critical errors

### Metrics
- **API Response Times**: Track HERE API performance
- **Cache Hit Rates**: Monitor caching effectiveness
- **Error Rates**: Track API failure rates
- **Request Volume**: Monitor API usage

## Troubleshooting

### Common Issues

1. **HERE API Errors**
   - Check API key validity
   - Verify network connectivity
   - Review API rate limits

2. **Invalid Coordinates**
   - Ensure latitude/longitude are valid decimal degrees
   - Check coordinate format and precision

3. **Transportation Mode Issues**
   - Use correct enum values (DRIVING, WALKING, PUBLIC_TRANSPORT, BICYCLING)
   - Verify mode mapping in HERE API service

4. **Cache Issues**
   - Clear cache if data appears stale
   - Check cache duration settings
   - Verify cache storage permissions

### Debug Mode
Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### 1. Advanced Routing
- **Multi-stop Routes**: Support for multiple waypoints
- **Alternative Routes**: Provide multiple route options
- **Route Optimization**: Optimize for time, distance, or cost

### 2. Enhanced Transportation Modes
- **Scooter Sharing**: Integration with scooter services
- **Car Sharing**: Support for car-sharing platforms
- **Bike Sharing**: Integration with bike-sharing services

### 3. Real-time Updates
- **Live Traffic**: Real-time traffic condition updates
- **Public Transport**: Live departure and arrival times
- **Weather Integration**: Weather-based route adjustments

### 4. Machine Learning
- **Travel Time Prediction**: ML-based travel time estimates
- **Route Preference Learning**: Learn user route preferences
- **Anomaly Detection**: Detect unusual travel patterns

## Conclusion

The prediction times implementation provides a robust foundation for calculating travel times between properties and interest points. The system's modular design, comprehensive caching, and error handling ensure reliable performance while maintaining flexibility for future enhancements.

Key benefits:
- **Accurate Calculations**: HERE API integration for precise routing
- **Efficient Performance**: Intelligent caching and batch processing
- **Scalable Architecture**: Modular design for easy extension
- **Comprehensive Monitoring**: Detailed logging and error handling
