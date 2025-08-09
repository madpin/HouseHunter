#!/usr/bin/env python3
"""
Test script for prediction times functionality
This script tests the new prediction times feature for next Friday at 9am
"""

import asyncio
import sys
import os
from datetime import date

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.interest_points_service import InterestPointsService
from app.models.interest_points import TransportationMode

async def test_prediction_times():
    """Test the prediction times functionality"""
    print("🚗 Testing Prediction Times for Next Friday 9am")
    print("=" * 60)
    
    # Initialize the service
    service = InterestPointsService()
    
    # Get active interest points
    active_points = service.get_active_interest_points()
    print(f"📍 Found {len(active_points)} active interest points:")
    for point in active_points:
        print(f"   • {point.name} ({point.default_transportation_mode.value})")
    
    if not active_points:
        print("❌ No active interest points found. Please configure some in interest_points_config.json")
        return
    
    # Test coordinates (Dublin City Center)
    test_lat, test_lng = 53.3498, -6.2603
    test_address = "Test Property, Dublin"
    
    print(f"\n🏠 Testing predictions from: {test_address} ({test_lat}, {test_lng})")
    
    try:
        # Calculate predictions
        prediction_info = await service.calculate_predictions_for_property(
            test_lat, test_lng, test_address
        )
        
        if prediction_info and prediction_info.predictions:
            print(f"\n✅ Successfully calculated {len(prediction_info.predictions)} predictions for {prediction_info.prediction_date}:")
            
            # Transportation mode emojis
            transport_emojis = {
                "DRIVING": "🚗",
                "WALKING": "🚶",
                "PUBLIC_TRANSPORT": "🚌",
                "BICYCLING": "🚲",
                "TRUCK": "🚛",
                "TAXI": "🚕",
                "BUS": "🚌",
                "TRAIN": "🚆",
                "SUBWAY": "🚇",
                "TRAM": "🚊",
                "FERRY": "⛴️"
            }

            for prediction in prediction_info.predictions:
                point_name = prediction.destination_point_id
                interest_point = service.get_interest_point_by_id(prediction.destination_point_id)
                if interest_point:
                    point_name = interest_point.name
                
                mode_emoji = transport_emojis.get(prediction.transportation_mode.value.upper(), "🚗")
                
                print(f"   {mode_emoji} {point_name}: {prediction.duration_minutes}min ({prediction.distance_km}km)")
                print(f"      Depart: {prediction.departure_time} • Arrive: {prediction.arrival_time}")
        else:
            print("❌ No predictions calculated")
            
    except Exception as e:
        print(f"❌ Error calculating predictions: {e}")
    
    finally:
        # Clean up
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_prediction_times())
