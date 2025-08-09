#!/usr/bin/env python3
"""
Test script to diagnose HERE API connection issues
"""

import os
import sys
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

# Load environment variables
load_dotenv()

def test_here_api_connection():
    """Test HERE API connection and basic functionality"""
    
    print("🔍 Testing HERE API Connection...")
    print("=" * 50)
    
    # Check environment variables
    here_api_key = os.getenv("HERE_API_KEY")
    here_api_enabled = os.getenv("HERE_API_ENABLED", "false").lower() == "true"
    
    print(f"HERE_API_KEY: {'✅ Set' if here_api_key else '❌ Not set'}")
    print(f"HERE_API_ENABLED: {'✅ True' if here_api_enabled else '❌ False'}")
    
    if not here_api_key:
        print("\n❌ HERE_API_KEY environment variable is not set!")
        print("Please create a .env file with your HERE API key:")
        print("HERE_API_KEY=your_api_key_here")
        print("HERE_API_ENABLED=true")
        return False
    
    if not here_api_enabled:
        print("\n❌ HERE_API_ENABLED is set to false!")
        print("Please set HERE_API_ENABLED=true in your .env file")
        return False
    
    # Test basic API endpoints
    print("\n🌐 Testing API Endpoints...")
    
    # Test routing API
    base_url = "https://router.hereapi.com/v8"
    transit_url = "https://transit.router.hereapi.com/v8"
    
    # Test coordinates (Dublin City Centre to Indeed office)
    origin = (53.3498, -6.2603)  # Dublin City Centre
    destination = (53.34549242723791, -6.231834356978687)  # Indeed office
    
    # Test 1: Regular routing (driving)
    print("\n🚗 Testing regular routing (driving)...")
    try:
        url = f"{base_url}/routes"
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "transportMode": "car",
            "return": "summary,travelSummary",
            "apiKey": here_api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and data["routes"]:
                route = data["routes"][0]
                summary = route.get("summary", {})
                duration = summary.get("duration", 0) // 60
                distance = summary.get("length", 0) / 1000
                print(f"✅ Success! Duration: {duration}min, Distance: {distance:.1f}km")
            else:
                print("⚠️  API returned success but no routes found")
                print(f"Response: {data}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing regular routing: {e}")
    
    # Test 2: Public transit routing
    print("\n🚌 Testing public transit routing...")
    try:
        url = f"{transit_url}/routes"
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "return": "travelSummary,polyline,actions",
            "alternatives": 1,
            "changes": 3,
            "pedestrian[maxDistance]": 2000,
            "pedestrian[speed]": 1.4,
            "apiKey": here_api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and data["routes"]:
                route = data["routes"][0]
                print(f"✅ Success! Found {len(data['routes'])} route(s)")
                if "sections" in route:
                    print(f"Route has {len(route['sections'])} sections")
            else:
                print("⚠️  API returned success but no routes found")
                print(f"Response: {data}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing public transit routing: {e}")
    
    # Test 3: Matrix routing
    print("\n📊 Testing matrix routing...")
    try:
        url = f"{base_url}/matrix"
        params = {
            "origins": f"{origin[0]},{origin[1]}",
            "destinations": f"{destination[0]},{destination[1]}",
            "transportMode": "car",
            "return": "travelSummary",
            "apiKey": here_api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "matrix" in data:
                print("✅ Success! Matrix routing working")
            else:
                print("⚠️  API returned success but no matrix data")
                print(f"Response: {data}")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing matrix routing: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Testing complete!")
    
    return True

if __name__ == "__main__":
    test_here_api_connection()
