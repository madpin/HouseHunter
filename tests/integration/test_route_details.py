#!/usr/bin/env python3
"""
Test script for route details functionality
This script tests the enhanced prediction times with route details
"""

import asyncio
import sys
import os
from datetime import date

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.interest_points_service import InterestPointsService
from app.models.interest_points import TransportationMode

async def test_route_details():
    """Test the route details functionality"""
    print("🚗 Testing Route Details for Next Friday 9am")
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
                
                mode_emoji = transport_emojis.get(prediction.transportation_mode.value, "🚗")
                
                print(f"\n   {mode_emoji} {point_name}: {prediction.duration_minutes}min ({prediction.distance_km}km)")
                print(f"      Depart: {prediction.departure_time} • Arrive: {prediction.arrival_time}")
                
                # Display route details
                if prediction.route_details:
                    route_details = prediction.route_details
                    print(f"      Route: {prediction.route_summary}")
                    
                    if route_details.get("transport_legs"):
                        print(f"      Transport legs:")
                        for i, leg in enumerate(route_details["transport_legs"], 1):
                            print(f"        {i}. {leg.get('line', 'Unknown')} ({leg['duration_minutes']}min)")
                    
                    total_walking = route_details.get("total_walking_minutes", 0)
                    if total_walking > 0:
                        print(f"      Walking: {total_walking}min ({route_details.get('total_walking_distance_km', 0):.1f}km)")
                else:
                    print(f"      Route: {prediction.route_summary or 'Direct route'}")
        else:
            print("❌ No predictions calculated")
            
    except Exception as e:
        print(f"❌ Error calculating predictions: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_route_details())
