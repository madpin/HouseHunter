from typing import Optional, Dict, Any, List
from notion_client import Client
from app.models.property import Property, WebsiteListing, PropertyType, ListingStatus
from datetime import datetime
from app.config import config
from app.services.interest_points_service import InterestPointsService
from app.models.interest_points import PropertyPredictionInfo

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
        self.interest_points_service = InterestPointsService("config/interest_points_config.json")
        
        # Cache database properties to validate optional fields like "Route Details"
        self.database_properties = set()
        try:
            database = self.client.databases.retrieve(self.database_id)
            self.database_properties = set(database.get("properties", {}).keys())
        except Exception:
            # If we cannot retrieve database schema now, continue without cached properties
            # and avoid adding optional properties that might not exist
            self.database_properties = set()
    
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
    
    def _create_property_page_data(self, property_obj: Property, prediction_info: Optional[PropertyPredictionInfo] = None) -> Dict[str, Any]:
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
        
        # Add route details summary if we have predictions (either provided or computed safely)
        if (
            prediction_info is not None or (
                hasattr(property_obj, 'address') and 
                hasattr(property_obj.address, 'latitude') and 
                hasattr(property_obj.address, 'longitude') and
                property_obj.address.latitude is not None and 
                property_obj.address.longitude is not None
            )
        ):
            try:
                prediction_info_local = prediction_info
                # Only attempt to compute if not provided
                if prediction_info_local is None:
                    import asyncio
                    try:
                        # If a loop is already running, skip computing here to avoid runtime errors
                        asyncio.get_running_loop()
                        prediction_info_local = None
                    except RuntimeError:
                        # No running loop; safe to compute synchronously
                        property_address = f"{property_obj.address.city}, {property_obj.address.county or ''}"
                        prediction_info_local = asyncio.run(
                            self.interest_points_service.calculate_predictions_for_property(
                                property_obj.address.latitude,
                                property_obj.address.longitude,
                                property_address
                            )
                        )
                if prediction_info_local and prediction_info_local.predictions:
                    route_summaries = []
                    for prediction in prediction_info_local.predictions:
                        point_name = prediction.destination_point_id
                        interest_point = self.interest_points_service.get_interest_point_by_id(prediction.destination_point_id)
                        if interest_point:
                            point_name = interest_point.name
                        route_summary = f"{point_name}: {prediction.duration_minutes}min"
                        if prediction.route_details:
                            route_parts = []
                            for section in prediction.route_details:
                                section_type = section.get("type", "unknown")
                                if section_type == "transit":
                                    line = section.get("line", "")
                                    if line and line != "Unknown":
                                        route_parts.append(line)
                                    else:
                                        name = section.get("name", "Unknown")
                                        route_parts.append(name)
                                elif section_type == "pedestrian":
                                    duration = section.get("duration_minutes", 0)
                                    if duration > 0:
                                        if duration < 1:
                                            route_parts.append("walk")
                                        elif duration < 5:
                                            route_parts.append(f"{duration}m walk")
                                        else:
                                            route_parts.append(f"{duration}m walk")
                            if route_parts:
                                route_summary += f" ({' + '.join(route_parts)})"
                        route_summaries.append(route_summary)
                    if route_summaries and "Route Details" in self.database_properties:
                        properties["Route Details"] = {
                            "rich_text": [
                                {"text": {"content": " | ".join(route_summaries)}}
                            ]
                        }
            except Exception:
                # Continue without route details if any error occurs
                pass
        
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
        
        # Add Transportation section if coordinates are available
        if (
            prediction_info is not None or (
                hasattr(property_obj, 'address') and 
                hasattr(property_obj.address, 'latitude') and 
                hasattr(property_obj.address, 'longitude') and
                property_obj.address.latitude is not None and 
                property_obj.address.longitude is not None
            )
        ):
            try:
                prediction_info_local = prediction_info
                # Only compute if not provided and safe to run
                if prediction_info_local is None:
                    import asyncio
                    try:
                        asyncio.get_running_loop()
                        prediction_info_local = None
                    except RuntimeError:
                        property_address = f"{property_obj.address.city}, {property_obj.address.county or ''}"
                        prediction_info_local = asyncio.run(
                            self.interest_points_service.calculate_predictions_for_property(
                                property_obj.address.latitude,
                                property_obj.address.longitude,
                                property_address
                            )
                        )
                if prediction_info_local and prediction_info_local.predictions:
                    # Add Transportation section heading
                    children.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"🚦 Transportation"}
                                }
                            ]
                        }
                    })
                    
                    # Add description
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "Routes to key locations from this property (departing next Friday at 09:00):"}
                                }
                            ]
                        }
                    })
                    
                    for prediction in prediction_info_local.predictions:
                        # Get interest point name
                        point_name = prediction.destination_point_id
                        interest_point = self.interest_points_service.get_interest_point_by_id(prediction.destination_point_id)
                        if interest_point:
                            point_name = interest_point.name
                        
                        # Get transportation mode emoji
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
                        mode_emoji = transport_emojis.get(prediction.transportation_mode.value, "🚗")
                        
                        # Build simple route info summary (from list of sections)
                        route_info = ""
                        if prediction.route_details and isinstance(prediction.route_details, list):
                            transit_lines = []
                            total_walking = 0
                            for section in prediction.route_details:
                                if section.get("type") == "transit":
                                    line = section.get("line") or section.get("name")
                                    if line and line != "Unknown":
                                        transit_lines.append(line)
                                elif section.get("type") == "pedestrian":
                                    total_walking += section.get("duration_minutes", 0)
                            if transit_lines:
                                route_info += f" • {' + '.join(transit_lines)}"
                            if total_walking > 0:
                                if total_walking < 1:
                                    route_info += " • short walk"
                                elif total_walking < 5:
                                    route_info += f" • {total_walking}min walk"
                                else:
                                    route_info += f" • {total_walking}min walking"
                        
                        # Use route summary if available, otherwise use route_info (kept for future use)
                        route_display = prediction.route_summary if prediction.route_summary else route_info
                        
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
                        
                        # Summary bullet per destination
                        prediction_text = (
                            f"• {mode_emoji} {point_name}: "
                            f"{prediction.duration_minutes}min ({distance_display}){walking_info}"
                        )
                        
                        children.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": prediction_text}
                                    }
                                ]
                            }
                        })
                        
                        # Add route line and detailed route information if available
                        if prediction.route_details and len(prediction.route_details) > 0:
                            # Add route summary line
                            route_summary_text = f"Route to {point_name} • Depart: {prediction.departure_time} • Arrive: {prediction.arrival_time}"
                            children.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": route_summary_text}
                                        }
                                    ]
                                }
                            })
                            
                            # Add route details label line
                            children.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": f"Route Details to {point_name}:"}
                                        }
                                    ]
                                }
                            })
                            # Add route breakdown with better formatting
                            for i, section in enumerate(prediction.route_details, 1):
                                section_type = section.get("type", "unknown")
                                duration = section.get("duration_minutes", 0)
                                distance_m = section.get("distance_m", 0)
                                
                                if section_type == "transit":
                                    mode = section.get("mode", "unknown")
                                    name = section.get("name", "Unknown")
                                    line = section.get("line", "")
                                    
                                    # Mode-specific emojis
                                    mode_emojis = {
                                        "bus": "🚌",
                                        "train": "🚆", 
                                        "subway": "🚇",
                                        "tram": "🚊",
                                        "ferry": "⛴️",
                                        "lightRail": "🚊",
                                        "cityTrain": "🚆",
                                        "regionalTrain": "🚆",
                                        "intercityTrain": "🚆"
                                    }
                                    
                                    mode_emoji = mode_emojis.get(mode, "🚌")
                                    distance_km = distance_m / 1000
                                    distance_display = f"{distance_km:.1f}km" if distance_km >= 1.0 else f"{distance_km:.3f}km"
                                    
                                    if line and line != "Unknown":
                                        section_text = f"  {i}. {mode_emoji} {line} ({duration}min, {distance_display})"
                                    else:
                                        section_text = f"  {i}. {mode_emoji} {name} ({duration}min, {distance_display})"
                                        
                                elif section_type == "pedestrian":
                                    distance_km = distance_m / 1000
                                    distance_display = f"{distance_km:.1f}km" if distance_km >= 1.0 else f"{distance_km:.3f}km"
                                    section_text = f"  {i}. 🚶 Walking ({duration}min, {distance_display})"
                                    
                                else:
                                    section_text = f"  {i}. {section_type.title()} ({duration}min)"
                                
                                children.append({
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {"content": section_text}
                                            }
                                        ]
                                    }
                                })
                            
                            # Add enhanced summary line
                            total_walking = sum(s.get("duration_minutes", 0) for s in prediction.route_details if s.get("type") == "pedestrian")
                            total_transit = sum(s.get("duration_minutes", 0) for s in prediction.route_details if s.get("type") == "transit")
                            
                            if total_walking > 0 and total_transit > 0:
                                summary_text = f"📊 Summary: {total_transit}min transit + {total_walking}min walking = {prediction.duration_minutes}min total"
                            elif total_walking > 0:
                                summary_text = f"📊 Summary: {total_walking}min walking = {prediction.duration_minutes}min total"
                            elif total_transit > 0:
                                summary_text = f"📊 Summary: {total_transit}min transit = {prediction.duration_minutes}min total"
                            else:
                                summary_text = f"📊 Total time: {prediction.duration_minutes}min"
                                
                            children.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": summary_text}
                                        }
                                    ]
                                }
                            })
                            
                            # Add spacing
                            children.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": ""}
                                        }
                                    ]
                                }
                            })
                    
            except Exception:
                # If prediction calculation fails, just continue without it
                pass
        
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
    
    async def save_property_to_notion(self, property_obj: Property, prediction_info: Optional[PropertyPredictionInfo] = None) -> Dict[str, Any]:
        """
        Save a property to Notion database
        
        Args:
            property_obj: Property object to save
            
        Returns:
            Notion API response with created page details
        """
        try:
            page_data = self._create_property_page_data(property_obj, prediction_info)
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