#!/usr/bin/env python3
"""
Test script for interest points service with public transport
"""

import asyncio
import os
import sys
import time
from typing import List, Tuple

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.interest_points_service import InterestPointsService

async def test_interest_points():
    """Test interest points service with public transport"""
    
    print("🏠 Testing Interest Points Service...")
    
    # Initialize service
    service = InterestPointsService()
    
    # Get all interest points
    points = service.get_all_interest_points()
    print(f"📍 Loaded {len(points)} interest points:")
    
    for point in points:
        print(f"  • {point.name} ({point.id})")
        print(f"    Location: {point.latitude}, {point.longitude}")
        print(f"    Transport: {point.default_transportation_mode.value}")
        print()
    
    # Test prediction calculation for multiple property locations
    test_locations = [
        {
            "name": "Dublin City Centre",
            "lat": 53.3498,
            "lng": -6.2603,
            "address": "Sample Property, Dublin City Centre"
        },
        {
            "name": "Rathmines",
            "lat": 53.3201,
            "lng": -6.2677,
            "address": "Sample Property, Rathmines, Dublin"
        },
        {
            "name": "Dundrum",
            "lat": 53.2921,
            "lng": -6.2456,
            "address": "Sample Property, Dundrum, Dublin"
        }
    ]
    
    for location in test_locations:
        print(f"🚌 Testing prediction calculation for {location['name']}...")
        print(f"📍 Property location: {location['lat']}, {location['lng']}")
        
        start_time = time.time()
        
        try:
            prediction_info = await service.calculate_predictions_for_property(
                location['lat'], location['lng'], location['address']
            )
            
            calculation_time = time.time() - start_time
            
            if prediction_info and prediction_info.predictions:
                print(f"✅ Successfully calculated {len(prediction_info.predictions)} predictions in {calculation_time:.2f}s")
                print(f"📅 Prediction date: {prediction_info.prediction_date}")
                print()
                
                # Sort predictions by duration
                sorted_predictions = sorted(prediction_info.predictions, key=lambda x: x.duration_minutes)
                
                for i, prediction in enumerate(sorted_predictions, 1):
                    # Get destination point details
                    dest_point = service.get_interest_point_by_id(prediction.destination_point_id)
                    dest_name = dest_point.name if dest_point else prediction.destination_point_id
                    
                    # Format distance with one decimal place (unless less than 1km)
                    distance_display = f"{prediction.distance_km:.1f}km" if prediction.distance_km >= 1.0 else f"{prediction.distance_km:.3f}km"
                    
                    # Add walking distance information if available
                    walking_info = ""
                    if hasattr(prediction, 'total_walking_distance_km') and prediction.total_walking_distance_km > 0:
                        walking_distance = prediction.total_walking_distance_km
                        if walking_distance >= 1.0:
                            walking_info = f" (🚶 {walking_distance:.1f}km walking)"
                        else:
                            walking_info = f" (🚶 {walking_distance:.3f}km walking)"
                    elif prediction.route_details:
                        # Fallback to route details for walking info
                        total_walking = 0
                        for section in prediction.route_details:
                            if section.get("type") == "pedestrian":
                                total_walking += section.get("duration_minutes", 0)
                        if total_walking > 0:
                            walking_info = f" (🚶 {total_walking}min walking)"
                    
                    print(f"  {i}. 🎯 To: {dest_name}")
                    print(f"     🚌 Mode: {prediction.transportation_mode.value}")
                    print(f"     ⏱️  Duration: {prediction.duration_minutes}min")
                    print(f"     📏 Distance: {distance_display}{walking_info}")
                    print(f"     🚀 Departure: {prediction.departure_time}")
                    print(f"     🏁 Arrival: {prediction.arrival_time}")
                    
                    if prediction.route_details:
                        print(f"     🛣️  Route details: {len(prediction.route_details)} sections")
                        for section in prediction.route_details:
                            section_type = section.get("type", "unknown")
                            duration = section.get("duration_minutes", 0)
                            if section_type == "transit":
                                mode = section.get("mode", "unknown")
                                name = section.get("name", "Unknown")
                                print(f"        • {section_type}: {mode} {name} ({duration}min)")
                            else:
                                print(f"        • {section_type}: {duration}min")
                    print()
            else:
                print("⚠️  No predictions calculated")
                
        except Exception as e:
            print(f"❌ Error calculating predictions: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 80)
    
    # Test specific interest point queries
    print("🔍 Testing specific interest point queries...")
    
    # Test by category
    transport_points = service.get_interest_points_by_category("transport")
    print(f"🚇 Transport points: {len(transport_points)}")
    for point in transport_points:
        print(f"  • {point.name}")
    
    # Test by ID
    airport_point = service.get_interest_point_by_id("dublin_airport")
    if airport_point:
        print(f"✈️  Found airport: {airport_point.name} at {airport_point.latitude}, {airport_point.longitude}")
    
    # Test active vs inactive
    active_points = service.get_active_interest_points()
    print(f"✅ Active points: {len(active_points)}")
    
    print("\n🎉 Interest Points Service test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_interest_points()) 