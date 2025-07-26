#!/usr/bin/env python3
"""
Script to set up Notion database with the correct properties for HouseHunter API
"""

import os
import sys
from notion_client import Client
from typing import Dict, Any, List

def get_notion_client():
    """Get Notion client with credentials from environment"""
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token:
        print("❌ NOTION_TOKEN environment variable is not set")
        sys.exit(1)
    
    if not database_id:
        print("❌ NOTION_DATABASE_ID environment variable is not set")
        sys.exit(1)
    
    return Client(auth=notion_token), database_id

def get_required_properties() -> Dict[str, Dict[str, Any]]:
    """Get the required properties for the HouseHunter database"""
    return {
        # Note: Title property is handled separately since databases can only have one title property
        "Address": {
            "type": "rich_text",
            "rich_text": {}
        },
        "Property Type": {
            "type": "select",
            "select": {
                "options": [
                    {"name": "House", "color": "blue"},
                    {"name": "Apartment", "color": "green"},
                    {"name": "Duplex", "color": "yellow"},
                    {"name": "Townhouse", "color": "orange"},
                    {"name": "Bungalow", "color": "purple"},
                    {"name": "Cottage", "color": "pink"},
                    {"name": "Penthouse", "color": "red"},
                    {"name": "Studio", "color": "gray"},
                    {"name": "Land", "color": "brown"},
                    {"name": "Commercial", "color": "default"}
                ]
            }
        },
        "City": {
            "type": "rich_text",
            "rich_text": {}
        },
        "County": {
            "type": "rich_text",
            "rich_text": {}
        },
        "Bedrooms": {
            "type": "number",
            "number": {
                "format": "number"
            }
        },
        "Bathrooms": {
            "type": "number",
            "number": {
                "format": "number"
            }
        },
        "Area (sqm)": {
            "type": "number",
            "number": {
                "format": "number"
            }
        },
        "Price": {
            "type": "rich_text",
            "rich_text": {}
        },
        "Energy Rating": {
            "type": "rich_text",
            "rich_text": {}
        },
        "Year Built": {
            "type": "number",
            "number": {
                "format": "number"
            }
        },
        "Status": {
            "type": "select",
            "select": {
                "options": [
                    {"name": "Active", "color": "green"},
                    {"name": "Inactive", "color": "red"}
                ]
            }
        },
        "Date Added": {
            "type": "date",
            "date": {}
        }
    }

def get_optional_properties() -> Dict[str, Dict[str, Any]]:
    """Get the optional properties for the HouseHunter database"""
    return {
        "Lot Size (sqm)": {
            "type": "number",
            "number": {
                "format": "number"
            }
        },
        "New Build": {
            "type": "checkbox",
            "checkbox": {}
        },
        "Furnished": {
            "type": "checkbox",
            "checkbox": {}
        },
        "Parking": {
            "type": "rich_text",
            "rich_text": {}
        },
        "Heating": {
            "type": "rich_text",
            "rich_text": {}
        }
    }

def check_existing_properties(client: Client, database_id: str) -> List[str]:
    """Check what properties already exist in the database"""
    try:
        database = client.databases.retrieve(database_id)
        existing_properties = list(database["properties"].keys())
        print(f"✅ Found existing properties: {', '.join(existing_properties)}")
        return existing_properties
    except Exception as e:
        print(f"❌ Error retrieving database: {e}")
        return []

def create_missing_properties(client: Client, database_id: str, existing_properties: List[str]):
    """Create missing properties in the database"""
    all_required_properties = {**get_required_properties(), **get_optional_properties()}
    
    # Find missing properties
    missing_properties = {}
    for prop_name, prop_config in all_required_properties.items():
        if prop_name not in existing_properties:
            missing_properties[prop_name] = prop_config
    
    if not missing_properties:
        print("✅ All required properties already exist!")
        return
    
    print(f"📝 Creating {len(missing_properties)} missing properties...")
    
    # Update database with new properties
    try:
        update_data = {"properties": missing_properties}
        client.databases.update(database_id, **update_data)
        print("✅ Successfully created missing properties!")
        
        # List the newly created properties
        for prop_name in missing_properties.keys():
            print(f"   ✅ Created: {prop_name}")
            
    except Exception as e:
        print(f"❌ Error creating properties: {e}")
        print("💡 Make sure your Notion integration has 'Can edit' permissions on the database")

def main():
    """Main function to set up the Notion database"""
    print("🏠 HouseHunter Notion Database Setup")
    print("=" * 50)
    
    # Get Notion client
    client, database_id = get_notion_client()
    
    print(f"📊 Database ID: {database_id}")
    
    # Check existing properties
    existing_properties = check_existing_properties(client, database_id)
    
    # Create missing properties
    create_missing_properties(client, database_id, existing_properties)
    
    print("\n" + "=" * 50)
    print("🎉 Database setup completed!")
    print("\nNext steps:")
    print("1. Verify the properties were created in your Notion database")
    print("2. Test the API with: curl http://localhost:32781/notion/database/info")
    print("3. Try ingesting a property: curl -X POST http://localhost:32781/notion/properties/ingest-and-save -H 'Content-Type: application/json' -d '{\"url\": \"https://www.daft.ie/for-sale/house-18-rosan-glas-rahoon-co-galway/6231936\"}'")

if __name__ == "__main__":
    main() 