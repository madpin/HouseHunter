#!/usr/bin/env python3
"""
Test script to verify HERE API connection is working.
Run this script to test if your HERE_API_KEY is properly configured and working.
"""

import asyncio
import aiohttp
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.here_api_service import HereApiService
from app.models.interest_points import TransportationMode
from app.config import config

async def test_here_api_connection():
    """Test HERE API connection with a simple distance calculation"""
    print("🔧 Testing HERE API Connection...")
    print("=" * 50)
    
    # Check if HERE API is configured
    if not config.HERE_API_KEY:
        print("❌ HERE_API_KEY not found in environment variables")
        print("   Please add HERE_API_KEY to your .env file")
        return False
    
    if not config.HERE_API_ENABLED:
        print("⚠️  HERE_API_ENABLED is set to false")
        print("   Please set HERE_API_ENABLED=true in your .env file")
        print("   Continuing with test anyway...")
    
    print(f"✅ HERE_API_KEY found: {config.HERE_API_KEY[:8]}...")
    
    # Test coordinates (Dublin City Center to Dublin Airport)
    origin_lat, origin_lng = 53.3498, -6.2603  # Dublin City Center
    dest_lat, dest_lng = 53.4213, -6.2701      # Dublin Airport
    
    print(f"\n📍 Testing distance calculation:")
    print(f"   From: Dublin City Center ({origin_lat}, {origin_lng})")
    print(f"   To: Dublin Airport ({dest_lat}, {dest_lng})")
    print(f"   Mode: Driving")
    
    try:
        # Create HERE API service
        here_service = HereApiService(config.HERE_API_KEY)
        
        # Test the connection
        result = here_service.get_route_summary(
            (origin_lat, origin_lng), (dest_lat, dest_lng), TransportationMode.DRIVING
        )
        
        if result:
            print(f"\n✅ HERE API connection successful!")
            print(f"   Route data received: {len(result)} keys")
            
            if "routes" in result and result["routes"]:
                route = result["routes"][0]
                summary = route.get("summary", {})
                
                distance_km = summary.get("length", 0) / 1000
                duration_minutes = summary.get("duration", 0) / 60
                
                print(f"   Distance: {distance_km:.2f} km")
                print(f"   Duration: {duration_minutes:.0f} minutes")
                print(f"   Transportation Mode: Driving")
            
            return True
        else:
            print(f"\n❌ HERE API returned no result")
            print(f"   This could indicate an API key issue or network problem")
            return False
            
    except Exception as e:
        print(f"\n❌ HERE API connection failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Provide helpful error messages
        if "401" in str(e) or "Unauthorized" in str(e):
            print(f"   💡 This usually means your HERE_API_KEY is invalid or expired")
        elif "403" in str(e) or "Forbidden" in str(e):
            print(f"   💡 This usually means your HERE_API_KEY doesn't have the required permissions")
        elif "429" in str(e) or "Too Many Requests" in str(e):
            print(f"   💡 Rate limit exceeded - try again later")
        elif "timeout" in str(e).lower():
            print(f"   💡 Network timeout - check your internet connection")
        
        return False
    
    finally:
        # Clean up - no async close needed for synchronous service
        pass

async def test_here_api_direct_request():
    """Test HERE API with a direct HTTP request to verify the API key"""
    print(f"\n🔍 Testing HERE API with direct HTTP request...")
    print("=" * 50)
    
    if not config.HERE_API_KEY:
        print("❌ HERE_API_KEY not found - skipping direct test")
        return False
    
    # Test coordinates
    origin_lat, origin_lng = 53.3498, -6.2603  # Dublin City Center
    dest_lat, dest_lng = 53.4213, -6.2701      # Dublin Airport
    
    url = "https://router.hereapi.com/v8/routes"
    params = {
        "apiKey": config.HERE_API_KEY,
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "transportMode": "car",
        "return": "summary,travelSummary"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                print(f"   Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    if "routes" in data and data["routes"]:
                        route = data["routes"][0]
                        summary = route.get("summary", {})
                        
                        distance_km = summary.get("length", 0) / 1000
                        duration_minutes = summary.get("duration", 0) / 60
                        
                        print(f"   ✅ Direct API call successful!")
                        print(f"   Distance: {distance_km:.2f} km")
                        print(f"   Duration: {duration_minutes:.0f} minutes")
                        return True
                    else:
                        print(f"   ⚠️  API returned no routes")
                        print(f"   Response: {data}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"   ❌ API call failed with status {response.status}")
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Direct API call failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🚀 HERE API Connection Test")
    print("=" * 50)
    
    # Test 1: Service-based test
    service_success = await test_here_api_connection()
    
    # Test 2: Direct API test
    direct_success = await test_here_api_direct_request()
    
    # Summary
    print(f"\n📊 Test Summary:")
    print("=" * 50)
    print(f"   Service-based test: {'✅ PASSED' if service_success else '❌ FAILED'}")
    print(f"   Direct API test: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    
    if service_success and direct_success:
        print(f"\n🎉 All tests passed! Your HERE API connection is working correctly.")
    elif service_success or direct_success:
        print(f"\n⚠️  Partial success. One test passed, one failed.")
        print(f"   This might indicate a configuration issue in the service layer.")
    else:
        print(f"\n❌ All tests failed. Please check your HERE_API_KEY configuration.")
        print(f"   Make sure:")
        print(f"   1. HERE_API_KEY is set in your .env file")
        print(f"   2. The API key is valid and active")
        print(f"   3. The API key has the required permissions")
        print(f"   4. Your internet connection is working")

if __name__ == "__main__":
    asyncio.run(main())
