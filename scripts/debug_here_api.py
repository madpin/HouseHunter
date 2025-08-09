#!/usr/bin/env python3
"""
Debug script to examine HERE API response structure
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_here_api_responses():
    """Debug HERE API responses to understand the structure"""
    
    here_api_key = os.getenv("HERE_API_KEY")
    if not here_api_key:
        print("❌ HERE_API_KEY not set")
        return
    
    print("🔍 Debugging HERE API Responses...")
    print("=" * 60)
    
    # Test coordinates (Dublin City Centre to Indeed office)
    origin = (53.3498, -6.2603)  # Dublin City Centre
    destination = (53.34549242723791, -6.231834356978687)  # Indeed office
    
    # Test 1: Regular routing (driving)
    print("\n🚗 Testing regular routing (driving)...")
    try:
        url = "https://router.hereapi.com/v8/routes"
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
            print("✅ API Response Structure:")
            print(json.dumps(data, indent=2))
            
            # Check for routes
            if "routes" in data and data["routes"]:
                route = data["routes"][0]
                print(f"\n📋 First Route Structure:")
                print(json.dumps(route, indent=2))
                
                # Check summary
                if "summary" in route:
                    summary = route["summary"]
                    print(f"\n📊 Summary Data:")
                    print(f"Duration: {summary.get('duration')}")
                    print(f"Length: {summary.get('length')}")
                    print(f"Base Duration: {summary.get('baseDuration')}")
                    print(f"Traffic Delay: {summary.get('trafficDelay')}")
                else:
                    print("❌ No 'summary' found in route")
                    
                # Check travelSummary
                if "travelSummary" in route:
                    travel_summary = route["travelSummary"]
                    print(f"\n🚗 Travel Summary Data:")
                    print(f"Duration: {travel_summary.get('duration')}")
                    print(f"Length: {travel_summary.get('length')}")
                    print(f"Base Duration: {travel_summary.get('baseDuration')}")
                    print(f"Traffic Delay: {travel_summary.get('trafficDelay')}")
                else:
                    print("❌ No 'travelSummary' found in route")
            else:
                print("❌ No routes found in response")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Public transit routing
    print("\n" + "=" * 60)
    print("🚌 Testing public transit routing...")
    try:
        url = "https://transit.router.hereapi.com/v8/routes"
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
            print("✅ API Response Structure:")
            print(json.dumps(data, indent=2))
            
            if "routes" in data and data["routes"]:
                route = data["routes"][0]
                print(f"\n📋 First Route Structure:")
                print(json.dumps(route, indent=2))
                
                # Check sections
                if "sections" in route:
                    sections = route["sections"]
                    print(f"\n🔗 Route Sections ({len(sections)} total):")
                    for i, section in enumerate(sections):
                        print(f"\nSection {i+1}:")
                        print(f"  Type: {section.get('type')}")
                        if "travelSummary" in section:
                            ts = section["travelSummary"]
                            print(f"  Duration: {ts.get('duration')}")
                            print(f"  Length: {ts.get('length')}")
                        else:
                            print(f"  No travelSummary")
                else:
                    print("❌ No 'sections' found in route")
            else:
                print("❌ No routes found in response")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Debug complete!")

if __name__ == "__main__":
    debug_here_api_responses()
