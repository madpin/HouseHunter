#!/usr/bin/env python3
"""
Test script to verify the interest points service works with the fixed HERE API
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

async def test_interest_points_service():
    """Test the interest points service with fixed HERE API"""
    
    try:
        from app.services.interest_points_service import InterestPointsService
        
        print("🔍 Testing Interest Points Service...")
        print("=" * 50)
        
        # Check environment variables
        here_api_key = os.getenv("HERE_API_KEY")
        if not here_api_key:
            print("❌ HERE_API_KEY not set")
            return False
        
        # Create service instance with correct config path
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'interest_points_config.json')
        interest_points_service = InterestPointsService(config_path)
        
        # Test coordinates (Dublin City Centre)
        property_lat, property_lng = 53.3498, -6.2603
        property_address = "Dublin City Centre, Co. Dublin, Ireland"
        
        print(f"📍 Testing property at ({property_lat}, {property_lng})")
        print(f"📍 Address: {property_address}")
        
        # Get active interest points
        active_points = interest_points_service.get_active_interest_points()
        print(f"\n🎯 Found {len(active_points)} active interest points:")
        for point in active_points:
            print(f"  • {point.name} ({point.id}) - {point.default_transportation_mode.value}")
            print(f"    Location: ({point.latitude}, {point.longitude})")
        
        # Calculate predictions for the property
        print(f"\n🚀 Calculating predictions for next Friday 9am...")
        try:
            prediction_info = await interest_points_service.calculate_predictions_for_property(
                property_lat, property_lng, property_address
            )
            
            if prediction_info and prediction_info.predictions:
                print(f"✅ Success! Calculated {len(prediction_info.predictions)} predictions:")
                
                for prediction in prediction_info.predictions:
                    print(f"\n  🎯 {prediction.route_summary}")
                    print(f"    Transportation: {prediction.transportation_mode.value}")
                    print(f"    Duration: {prediction.duration_minutes} minutes")
                    print(f"    Distance: {prediction.distance_km:.1f} km")
                    print(f"    Departure: {prediction.departure_time}")
                    print(f"    Arrival: {prediction.arrival_time}")
                    
                    if hasattr(prediction, 'total_walking_minutes') and prediction.total_walking_minutes:
                        print(f"    Walking: {prediction.total_walking_minutes} min")
                    if hasattr(prediction, 'total_walking_distance_km') and prediction.total_walking_distance_km:
                        print(f"    Walking distance: {prediction.total_walking_distance_km:.1f} km")
                        
            else:
                print("❌ No predictions calculated")
                print(f"Prediction info: {prediction_info}")
                
        except Exception as e:
            print(f"❌ Error calculating predictions: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("🏁 Testing complete!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_interest_points_service())
