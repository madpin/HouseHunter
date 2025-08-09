#!/usr/bin/env python3
"""
Debug script to test interest points service and identify the issue
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.interest_points_service import InterestPointsService
from app.services.here_api_service import HereApiService

# Load environment variables
load_dotenv()

async def test_interest_points_service():
    """Test the interest points service to identify the issue"""
    
    here_api_key = os.getenv("HERE_API_KEY")
    if not here_api_key:
        print("❌ HERE_API_KEY not set")
        return
    
    print("🔍 Testing Interest Points Service...")
    print("=" * 60)
    
    # Initialize services
    interest_points_service = InterestPointsService("config/interest_points_config.json")
    here_service = HereApiService(here_api_key)
    
    # Test coordinates (Dublin City Centre)
    test_lat = 53.3498
    test_lng = -6.2603
    test_address = "Dublin City Centre, Co. Dublin"
    
    print(f"📍 Testing with coordinates: {test_lat}, {test_lng}")
    print(f"🏠 Address: {test_address}")
    
    # Check if interest points are loaded
    active_points = interest_points_service.get_active_interest_points()
    print(f"🎯 Active interest points: {len(active_points)}")
    
    for point in active_points:
        print(f"  • {point.id}: {point.name} ({point.default_transportation_mode.value})")
    
    if not active_points:
        print("❌ No active interest points found!")
        return
    
    # Test the calculate_predictions_for_property method
    print("\n🚗 Testing calculate_predictions_for_property...")
    try:
        prediction_info = await interest_points_service.calculate_predictions_for_property(
            test_lat, test_lng, test_address
        )
        
        if prediction_info:
            print(f"✅ Prediction info created successfully")
            print(f"📊 Property ID: {prediction_info.property_id}")
            print(f"📍 Property Address: {prediction_info.property_address}")
            print(f"📅 Prediction Date: {prediction_info.prediction_date}")
            print(f"🔢 Number of predictions: {len(prediction_info.predictions)}")
            
            if prediction_info.predictions:
                for i, prediction in enumerate(prediction_info.predictions):
                    print(f"\n  Prediction {i+1}:")
                    print(f"    Destination: {prediction.destination_point_id}")
                    print(f"    Mode: {prediction.transportation_mode.value}")
                    print(f"    Duration: {prediction.duration_minutes} min")
                    print(f"    Distance: {prediction.distance_km:.3f} km")
                    print(f"    Departure: {prediction.departure_time}")
                    print(f"    Arrival: {prediction.arrival_time}")
                    
                    if prediction.route_details:
                        print(f"    Route details: {len(prediction.route_details)} sections")
                    else:
                        print(f"    Route details: None")
            else:
                print("❌ No predictions in the prediction info")
        else:
            print("❌ Prediction info is None")
            
    except Exception as e:
        print(f"❌ Error in calculate_predictions_for_property: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    # Test individual HERE API calls
    print("\n" + "=" * 60)
    print("🔍 Testing individual HERE API calls...")
    
    for point in active_points[:2]:  # Test first 2 points
        print(f"\n🎯 Testing route to {point.name} ({point.id})")
        print(f"📍 Destination: {point.latitude}, {point.lng}")
        print(f"🚌 Mode: {point.default_transportation_mode.value}")
        
        try:
            prediction_data = await here_service.calculate_prediction_time(
                test_lat, test_lng,
                point.latitude, point.longitude,
                point.default_transportation_mode
            )
            
            if prediction_data:
                print(f"✅ HERE API call successful")
                print(f"📊 Distance: {prediction_data.get('distance_km', 'N/A')} km")
                print(f"⏱️ Duration: {prediction_data.get('duration_minutes', 'N/A')} min")
                print(f"🚗 Mode: {prediction_data.get('transport_mode', 'N/A')}")
                print(f"🕐 Departure: {prediction_data.get('departure_time', 'N/A')}")
                print(f"🕐 Arrival: {prediction_data.get('arrival_time', 'N/A')}")
                
                if prediction_data.get('route_details'):
                    print(f"🛣️ Route details: {len(prediction_data['route_details'])} sections")
                else:
                    print(f"🛣️ Route details: None")
            else:
                print(f"❌ HERE API call returned None")
                
        except Exception as e:
            print(f"❌ Error in HERE API call: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_interest_points_service())
