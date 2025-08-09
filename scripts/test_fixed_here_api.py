#!/usr/bin/env python3
"""
Test script to verify the fixed HERE API service
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

async def test_fixed_here_api():
    """Test the fixed HERE API service"""
    
    try:
        from app.services.here_api_service import HereApiService
        from app.models.interest_points import TransportationMode
        
        print("🔍 Testing Fixed HERE API Service...")
        print("=" * 50)
        
        # Check environment variables
        here_api_key = os.getenv("HERE_API_KEY")
        if not here_api_key:
            print("❌ HERE_API_KEY not set")
            return False
        
        # Create service instance
        here_service = HereApiService(here_api_key)
        
        # Test coordinates (Dublin City Centre to Indeed office)
        origin_lat, origin_lng = 53.3498, -6.2603  # Dublin City Centre
        dest_lat, dest_lng = 53.34549242723791, -6.231834356978687  # Indeed office
        
        print(f"📍 Testing route from ({origin_lat}, {origin_lng}) to ({dest_lat}, {dest_lng})")
        
        # Test 1: Driving mode
        print("\n🚗 Testing DRIVING mode...")
        try:
            result = await here_service.calculate_prediction_time(
                origin_lat, origin_lng, dest_lat, dest_lng, TransportationMode.DRIVING
            )
            
            if result:
                print("✅ Success!")
                print(f"  Duration: {result.get('duration_minutes')} minutes")
                print(f"  Distance: {result.get('distance_km', 0):.1f} km")
                print(f"  Departure: {result.get('departure_time')}")
                print(f"  Arrival: {result.get('arrival_time')}")
            else:
                print("❌ Failed to get prediction")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Public transport mode
        print("\n🚌 Testing PUBLIC_TRANSPORT mode...")
        try:
            result = await here_service.calculate_prediction_time(
                origin_lat, origin_lng, dest_lat, dest_lng, TransportationMode.PUBLIC_TRANSPORT
            )
            
            if result:
                print("✅ Success!")
                print(f"  Duration: {result.get('duration_minutes')} minutes")
                print(f"  Distance: {result.get('distance_km', 0):.1f} km")
                print(f"  Departure: {result.get('departure_time')}")
                print(f"  Arrival: {result.get('arrival_time')}")
                print(f"  Walking: {result.get('total_walking_minutes', 0)} min")
                print(f"  Walking distance: {result.get('total_walking_distance_km', 0):.1f} km")
            else:
                print("❌ Failed to get prediction")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Walking mode
        print("\n🚶 Testing WALKING mode...")
        try:
            result = await here_service.calculate_prediction_time(
                origin_lat, origin_lng, dest_lat, dest_lng, TransportationMode.WALKING
            )
            
            if result:
                print("✅ Success!")
                print(f"  Duration: {result.get('duration_minutes')} minutes")
                print(f"  Distance: {result.get('distance_km', 0):.1f} km")
                print(f"  Departure: {result.get('departure_time')}")
                print(f"  Arrival: {result.get('arrival_time')}")
            else:
                print("❌ Failed to get prediction")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 Testing complete!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_fixed_here_api())
