from typing import Optional, Dict, Any, List
from notion_client import Client
from app.models.property import Property, WebsiteListing, PropertyType, ListingStatus
from datetime import datetime
from app.config import config

class NotionService:
    """Service for interacting with Notion API to save property data"""
    
    def __init__(self, notion_token: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion service
        
        Args:
            notion_token: Notion integration token (defaults to NOTION_TOKEN env var)
            database_id: Notion database ID (defaults to NOTION_DATABASE_ID env var)
        """
        self.notion_token = notion_token or config.NOTION_TOKEN
        self.database_id = database_id or config.NOTION_DATABASE_ID
        
        if not self.notion_token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN environment variable or pass it to constructor.")
        
        if not self.database_id:
            raise ValueError("Notion database ID is required. Set NOTION_DATABASE_ID environment variable or pass it to constructor.")
        
        self.client = Client(auth=self.notion_token)
    
    def _format_price(self, price: float, currency: str = "EUR") -> str:
        """Format price for Notion display"""
        return f"{currency} {price:,.0f}"
    
    def _format_address(self, property_obj: Property) -> str:
        """Format address for Notion display"""
        addr = property_obj.address
        parts = [addr.street, addr.city]
        if addr.county:
            parts.append(addr.county)
        if addr.postal_code:
            parts.append(addr.postal_code)
        return ", ".join(parts)
    
    def _get_property_type_emoji(self, property_type: PropertyType) -> str:
        """Get emoji for property type"""
        emoji_map = {
            PropertyType.HOUSE: "🏠",
            PropertyType.APARTMENT: "🏢",
            PropertyType.DUPLEX: "🏘️",
            PropertyType.TOWNHOUSE: "🏘️",
            PropertyType.BUNGALOW: "🏡",
            PropertyType.COTTAGE: "🏚️",
            PropertyType.PENTHOUSE: "🏙️",
            PropertyType.STUDIO: "🏠",
            PropertyType.LAND: "🌍",
            PropertyType.COMMERCIAL: "🏢"
        }
        return emoji_map.get(property_type, "🏠")
    
    def _format_listings_info(self, listings: List[WebsiteListing]) -> str:
        """Format listings information for Notion"""
        if not listings:
            return "No listings"
        
        active_listings = [l for l in listings if l.status == ListingStatus.ACTIVE]
        if not active_listings:
            return "No active listings"
        
        info_parts = []
        for listing in active_listings:
            price_str = self._format_price(listing.price, listing.currency)
            info_parts.append(f"{listing.website.value}: {price_str}")
        
        return " | ".join(info_parts)
    
    def _create_property_page_data(self, property_obj: Property) -> Dict[str, Any]:
        """Create Notion page data for a property"""
        
        # Get primary listing for main details
        primary_listing = property_obj.primary_listing
        
        # Format property type with emoji
        property_type_emoji = self._get_property_type_emoji(property_obj.property_type)
        property_type_display = f"{property_type_emoji} {property_obj.property_type.value.title()}"
        
        # Create page properties
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": f"{property_type_display} - {self._format_address(property_obj)}"
                        }
                    }
                ]
            },
            "Address": {
                "rich_text": [
                    {
                        "text": {
                            "content": self._format_address(property_obj)
                        }
                    }
                ]
            },
            "Property Type": {
                "select": {
                    "name": property_obj.property_type.value.title()
                }
            },
            "City": {
                "rich_text": [
                    {
                        "text": {
                            "content": property_obj.address.city
                        }
                    }
                ]
            },
            "County": {
                "rich_text": [
                    {
                        "text": {
                            "content": property_obj.address.county or "N/A"
                        }
                    }
                ] if property_obj.address.county else []
            },
            "Bedrooms": {
                "number": property_obj.bedrooms
            },
            "Bathrooms": {
                "number": property_obj.bathrooms
            },
            "Area (sqm)": {
                "number": property_obj.area_sqm
            },
            "Price": {
                "rich_text": [
                    {
                        "text": {
                            "content": self._format_listings_info(property_obj.listings)
                        }
                    }
                ]
            },
            "Energy Rating": {
                "rich_text": [
                    {
                        "text": {
                            "content": property_obj.energy_rating or "N/A"
                        }
                    }
                ] if property_obj.energy_rating else []
            },
            "Year Built": {
                "number": property_obj.year_built
            },
            "Status": {
                "select": {
                    "name": "Active" if property_obj.active_listings else "Inactive"
                }
            },
            "Date Added": {
                "date": {
                    "start": property_obj.created_at.isoformat()
                }
            }
        }
        
        # Add optional fields if they exist
        if property_obj.lot_size_sqm:
            properties["Lot Size (sqm)"] = {"number": property_obj.lot_size_sqm}
        
        if property_obj.is_new_build is not None:
            properties["New Build"] = {"checkbox": property_obj.is_new_build}
        
        if property_obj.furnished is not None:
            properties["Furnished"] = {"checkbox": property_obj.furnished}
        
        if property_obj.parking:
            properties["Parking"] = {
                "rich_text": [{"text": {"content": property_obj.parking}}]
            }
        
        if property_obj.heating:
            properties["Heating"] = {
                "rich_text": [{"text": {"content": property_obj.heating}}]
            }
        
        # Create page content
        children = []
        
        # Add property description if available
        if primary_listing and primary_listing.description:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": primary_listing.description[:2000]  # Notion limit
                            }
                        }
                    ]
                }
            })
        
        # Add listings section
        if property_obj.listings:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Listings"}
                        }
                    ]
                }
            })
            
            for listing in property_obj.listings:
                price_str = self._format_price(listing.price, listing.currency)
                listing_text = f"• {listing.website.value.title()}: {price_str} - {listing.status.value}"
                if listing.listing_url:
                    listing_text += f" - {listing.listing_url}"
                
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": listing_text}
                            }
                        ]
                    }
                })
        
        # Add features section if available
        if primary_listing and primary_listing.features:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Features"}
                        }
                    ]
                }
            })
            
            for feature in primary_listing.features:
                feature_text = f"• {feature.name}"
                if feature.value:
                    feature_text += f": {feature.value}"
                
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": feature_text}
                            }
                        ]
                    }
                })
        
        return {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children
        }
    
    async def save_property_to_notion(self, property_obj: Property) -> Dict[str, Any]:
        """
        Save a property to Notion database
        
        Args:
            property_obj: Property object to save
            
        Returns:
            Notion API response with created page details
        """
        try:
            page_data = self._create_property_page_data(property_obj)
            response = self.client.pages.create(**page_data)
            
            return {
                "success": True,
                "notion_page_id": response["id"],
                "notion_page_url": response["url"],
                "property_id": property_obj.id,
                "message": "Property successfully saved to Notion"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "property_id": property_obj.id,
                "message": "Failed to save property to Notion"
            }
    
    async def check_database_exists(self) -> bool:
        """Check if the configured database exists and is accessible"""
        try:
            self.client.databases.retrieve(self.database_id)
            return True
        except Exception:
            return False
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get information about the configured database"""
        try:
            database = self.client.databases.retrieve(self.database_id)
            return {
                "success": True,
                "database_id": database["id"],
                "database_title": database["title"][0]["plain_text"] if database["title"] else "Untitled",
                "database_url": database["url"],
                "properties": list(database["properties"].keys())
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve database information"
            } 