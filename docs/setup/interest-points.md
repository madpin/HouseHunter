# Interest Points Setup Guide

## Overview
This guide explains how to set up and configure interest points for the HouseHunter application. Interest points are locations that are important for property evaluation, such as work locations, schools, transport hubs, etc.

## Features
- **Geographic Coordinates**: Latitude and longitude for precise location
- **Multiple Transportation Modes**: Driving, walking, public transport, cycling
- **Distance Calculations**: Real-time distance and travel time calculations
- **HERE API Integration**: Uses HERE Maps API for accurate routing
- **Caching**: Configurable caching for API responses
- **Priority System**: Configurable priority levels for different points

## Transportation Modes

The application supports the following transportation modes:

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

### 5. Truck (TRUCK)
- **Value**: `TRUCK`
- **Description**: Commercial vehicle routing
- **Best for**: Delivery planning, commercial operations
- **Features**: Truck-specific restrictions, weight limits

### 6. Taxi (TAXI)
- **Value**: `TAXI`
- **Description**: Taxi service routing
- **Best for**: Airport transfers, late-night travel
- **Features**: Taxi-specific routing

### 7. Bus (BUS)
- **Value**: `BUS`
- **Description**: Bus-only routing
- **Best for**: Local public transport
- **Features**: Bus stop routing, schedules

### 8. Train (TRAIN)
- **Value**: `TRAIN`
- **Description**: Train routing
- **Best for**: Inter-city travel, commuting
- **Features**: Station routing, schedules

### 9. Subway (SUBWAY)
- **Value**: `SUBWAY`
- **Description**: Underground/metro routing
- **Best for**: Urban commuting
- **Features**: Station routing, underground navigation

### 10. Tram (TRAM)
- **Value**: `TRAM`
- **Description**: Light rail/tram routing
- **Best for**: Urban transport
- **Features**: Tram stop routing, schedules

### 11. Ferry (FERRY)
- **Value**: `FERRY`
- **Description**: Ferry service routing
- **Best for**: Water crossings, island access
- **Features**: Port routing, schedules

## Configuration File Structure

The interest points are configured in `interest_points_config.json`:

```json
{
  "interest_points": [
    {
      "id": "work_location",
      "name": "My Work",
      "category": "work",
      "latitude": 53.3498,
      "longitude": -6.2603,
      "address": "123 Main Street, Dublin",
      "description": "Primary work location",
      "rating": 4.5,
      "opening_hours": "09:00-17:00",
      "phone": "+353 1 234 5678",
      "website": "https://company.com",
      "price_level": "$$",
      "photos": [],
      "tags": ["work", "office", "downtown"],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "is_active": true,
      "source": "manual",
      "external_id": null,
      "metadata": {},
      "transportation_mode": "DRIVING"
    }
  ],
  "settings": {
    "default_transportation_mode": "DRIVING",
    "cache_duration_hours": 24,
    "max_concurrent_requests": 10,
    "request_timeout_seconds": 30,
    "enable_traffic_info": true,
    "enable_route_details": false
  }
}
```

## Adding New Interest Points

### 1. Manual Configuration
Edit the `interest_points_config.json` file and add new entries:

```json
{
  "id": "new_point",
  "name": "New Location",
  "category": "shopping",
  "latitude": 53.3498,
  "longitude": -6.2603,
  "address": "New Address",
  "description": "Description of the location",
  "rating": 4.0,
  "opening_hours": "10:00-18:00",
  "phone": "+353 1 234 5678",
  "website": "https://example.com",
  "price_level": "$",
  "photos": [],
  "tags": ["shopping", "retail"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "is_active": true,
  "source": "manual",
  "external_id": null,
  "metadata": {},
  "transportation_mode": "DRIVING"
}
```

### 2. Programmatic Addition
Use the `InterestPointsService` to add points programmatically:

```python
from app.services.interest_points_service import InterestPointsService
from app.models.interest_points import InterestPoint, TransportationMode

service = InterestPointsService()

new_point = InterestPoint(
    id="new_point",
    name="New Location",
    category="shopping",
    latitude=53.3498,
    longitude=-6.2603,
    address="New Address",
    description="Description of the location",
    rating=4.0,
    opening_hours="10:00-18:00",
    phone="+353 1 234 5678",
    website="https://example.com",
    price_level="$",
    photos=[],
    tags=["shopping", "retail"],
    created_at="2024-01-01T00:00:00Z",
    updated_at="2024-01-01T00:00:00Z",
    is_active=True,
    source="manual",
    external_id=None,
    metadata={},
    default_transportation_mode=TransportationMode.DRIVING
)

service.add_interest_point(new_point)
service.save_configuration()
```

## HERE API Configuration

The application uses HERE Maps API for distance calculations. Ensure you have:

1. **API Key**: Valid HERE API key in your environment
2. **Transportation Modes**: Use the correct enum values (e.g., `DRIVING`, `PUBLIC_TRANSPORT`)
3. **Return Parameters**: The API uses `summary,travelSummary` for basic routing

## Testing

Test your interest points configuration:

```bash
python -m pytest tests/test_interest_points.py -v
```

## Troubleshooting

### Common Issues

1. **Invalid Transportation Mode**: Ensure you're using the correct enum values
2. **HERE API Errors**: Check your API key and network connectivity
3. **Coordinate Issues**: Verify latitude/longitude are valid decimal degrees

### Debug Mode

Enable debug logging to see detailed API requests:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Use Descriptive Names**: Clear, memorable names for interest points
2. **Categorize Points**: Group related points by category
3. **Regular Updates**: Keep coordinates and information current
4. **Transportation Mode**: Choose the most appropriate mode for each point
5. **Metadata**: Use metadata for additional context and filtering 