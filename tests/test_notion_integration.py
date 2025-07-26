#!/usr/bin/env python3
"""
Test script for Notion integration endpoints
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

async def test_notion_endpoints():
    """Test all Notion integration endpoints"""
    
    async with aiohttp.ClientSession() as session:
        print("🏠 Testing HouseHunter Notion Integration")
        print("=" * 50)
        
        # Test 1: Check database accessibility
        print("\n1. Testing database accessibility...")
        try:
            async with session.get(f"{BASE_URL}/notion/database/check") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Database check: {data['message']}")
                else:
                    print(f"❌ Database check failed: {response.status}")
                    error_data = await response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Database check error: {e}")
        
        # Test 2: Get database information
        print("\n2. Getting database information...")
        try:
            async with session.get(f"{BASE_URL}/notion/database/info") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Database info retrieved:")
                    print(f"   Title: {data.get('database_title', 'N/A')}")
                    print(f"   ID: {data.get('database_id', 'N/A')}")
                    print(f"   URL: {data.get('database_url', 'N/A')}")
                    print(f"   Properties: {', '.join(data.get('properties', []))}")
                else:
                    print(f"❌ Database info failed: {response.status}")
                    error_data = await response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Database info error: {e}")
        
        # Test 3: Ingest and save a property from URL
        print("\n3. Testing property ingestion and Notion save...")
        test_url = "https://www.daft.ie/property/example"  # Replace with real URL
        
        try:
            payload = {"url": test_url}
            async with session.post(
                f"{BASE_URL}/notion/properties/ingest-and-save",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Property ingested and saved to Notion:")
                    print(f"   Property ID: {data.get('property', {}).get('id', 'N/A')}")
                    print(f"   Notion Page ID: {data.get('notion_result', {}).get('notion_page_id', 'N/A')}")
                    print(f"   Notion URL: {data.get('notion_result', {}).get('notion_page_url', 'N/A')}")
                else:
                    print(f"❌ Property ingestion failed: {response.status}")
                    error_data = await response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Property ingestion error: {e}")
        
        # Test 4: Batch save properties (if you have existing properties)
        print("\n4. Testing batch save...")
        try:
            # This would require existing property IDs
            payload = {"property_ids": ["test_id_1", "test_id_2"]}
            async with session.post(
                f"{BASE_URL}/notion/properties/batch-save",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Batch save completed:")
                    print(f"   Total: {data.get('total_properties', 0)}")
                    print(f"   Successful: {data.get('successful', 0)}")
                    print(f"   Failed: {data.get('failed', 0)}")
                else:
                    print(f"❌ Batch save failed: {response.status}")
                    error_data = await response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Batch save error: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 Notion integration tests completed!")

async def test_with_real_data():
    """Test with a real property URL (replace with actual URL)"""
    
    # Example: Replace this with a real Daft.ie property URL
    real_property_url = "https://www.daft.ie/property/example"
    
    print(f"\n🔗 Testing with real property URL: {real_property_url}")
    
    async with aiohttp.ClientSession() as session:
        try:
            payload = {"url": real_property_url}
            async with session.post(
                f"{BASE_URL}/notion/properties/ingest-and-save",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Success! Property saved to Notion")
                    print(f"   Property: {data.get('property', {}).get('address', {}).get('street', 'N/A')}")
                    print(f"   Notion Page: {data.get('notion_result', {}).get('notion_page_url', 'N/A')}")
                else:
                    print(f"❌ Failed: {response.status}")
                    error_data = await response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Error: {e}")

def print_usage_examples():
    """Print usage examples for the Notion integration"""
    
    print("\n📖 Usage Examples:")
    print("=" * 50)
    
    print("\n1. Check if Notion database is accessible:")
    print("   curl http://localhost:8000/notion/database/check")
    
    print("\n2. Get database information:")
    print("   curl http://localhost:8000/notion/database/info")
    
    print("\n3. Ingest and save a property from URL:")
    print("   curl -X POST http://localhost:8000/notion/properties/ingest-and-save \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"url\": \"https://www.daft.ie/property/example\"}'")
    
    print("\n4. Save an existing property to Notion:")
    print("   curl -X POST http://localhost:8000/notion/properties/save \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"property_id\": \"your_property_id\"}'")
    
    print("\n5. Batch save multiple properties:")
    print("   curl -X POST http://localhost:8000/notion/properties/batch-save \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"property_ids\": [\"id1\", \"id2\", \"id3\"]}'")

if __name__ == "__main__":
    print("🚀 HouseHunter Notion Integration Test Script")
    print("Make sure the API is running on http://localhost:8000")
    print("Make sure NOTION_TOKEN and NOTION_DATABASE_ID are set")
    
    # Run basic tests
    asyncio.run(test_notion_endpoints())
    
    # Print usage examples
    print_usage_examples()
    
    # Uncomment the line below to test with a real property URL
    # asyncio.run(test_with_real_data()) 