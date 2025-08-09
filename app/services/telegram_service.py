import logging
import re
from typing import Optional, Dict, Any, List
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pydantic import HttpUrl, ValidationError

from app.config import config
from app.services.notion_service import NotionService
from app.services.property_service import PropertyService
from app.services.interest_points_service import InterestPointsService
from app.services.geocoding_service import GeocodingService
from app.scrapers.scraper_factory import ScraperFactory
from app.models.property import Property

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL.upper())
)
logger = logging.getLogger(__name__)

class TelegramService:
    """Service for handling Telegram bot interactions"""
    
    def __init__(self, 
                 bot_token: Optional[str] = None,
                 notion_service: Optional[NotionService] = None,
                 property_service: Optional[PropertyService] = None,
                 scraper_factory: Optional[ScraperFactory] = None,
                 interest_points_service: Optional[InterestPointsService] = None,
                 geocoding_service: Optional[GeocodingService] = None):
        """
        Initialize Telegram service
        
        Args:
            bot_token: Telegram bot token (defaults to TELEGRAM_BOT_TOKEN env var)
            notion_service: NotionService instance
            property_service: PropertyService instance  
            scraper_factory: ScraperFactory instance
            interest_points_service: InterestPointsService instance
            geocoding_service: GeocodingService instance
        """
        self.bot_token = bot_token or config.TELEGRAM_BOT_TOKEN
        if not self.bot_token:
            raise ValueError("Telegram bot token is required. Set TELEGRAM_BOT_TOKEN environment variable.")
        
        self.notion_service = notion_service or NotionService()
        self.property_service = property_service or PropertyService()
        self.scraper_factory = scraper_factory or ScraperFactory()
        self.interest_points_service = interest_points_service or InterestPointsService("config/interest_points_config.json")
        self.geocoding_service = geocoding_service or GeocodingService()
        
        self.application: Optional[Application] = None
        self.is_running = False
    
    def _is_url(self, text: str) -> bool:
        """Check if text contains a valid URL"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return bool(re.search(url_pattern, text))
    
    def _extract_urls(self, text: str) -> list[str]:
        """Extract all URLs from text"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    def _split_message(self, message: str, max_length: int = 4000) -> List[str]:
        """
        Split a long message into multiple parts that fit within Telegram's limits
        
        Args:
            message: The message to split
            max_length: Maximum length per message (default 4000 to be safe)
            
        Returns:
            List of message parts
        """
        if len(message) <= max_length:
            return [message]
        
        parts = []
        current_part = ""
        lines = message.split('\n')
        
        for line in lines:
            # If adding this line would exceed the limit
            if len(current_part) + len(line) + 1 > max_length:
                # Save current part if it's not empty
                if current_part.strip():
                    parts.append(current_part.strip())
                
                # Start new part with this line
                current_part = line
            else:
                # Add line to current part
                if current_part:
                    current_part += '\n' + line
                else:
                    current_part = line
        
        # Add the last part if it's not empty
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    async def _send_long_message(self, chat_id: int, message: str, parse_mode: str = None) -> List[Any]:
        """
        Send a potentially long message by splitting it if necessary
        
        Args:
            chat_id: The chat ID to send the message to
            message: The message to send
            parse_mode: Parse mode for the message
            
        Returns:
            List of sent message objects
        """
        if not self.application or not self.application.bot:
            logger.error("Bot not initialized, cannot send message")
            return []
        
        parts = self._split_message(message)
        sent_messages = []
        
        for i, part in enumerate(parts):
            try:
                if i == 0:
                    # First part - edit the existing processing message
                    # We'll need to handle this differently since we're editing
                    pass
                else:
                    # Additional parts - send as new messages
                    sent_msg = await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=part,
                        parse_mode=parse_mode
                    )
                    sent_messages.append(sent_msg)
            except Exception as e:
                logger.error(f"Failed to send message part {i+1}: {e}")
                # Try to send without parse_mode if it fails
                try:
                    sent_msg = await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=part
                    )
                    sent_messages.append(sent_msg)
                except Exception as e2:
                    logger.error(f"Failed to send message part {i+1} without parse_mode: {e2}")
        
        return sent_messages

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = (
            "🏠 Welcome to HouseHunter Bot! 🏠\n\n"
            "I can help you save property listings to your Notion database.\n\n"
            "📋 Available commands:\n"
            "/start - Show this welcome message\n"
            "/help - Get help information\n"
            "/status - Check bot and database status\n"
            "/supported - List supported property websites\n\n"
            "🔗 To add a property, simply send me a property URL from a supported website!\n\n"
            "Supported websites:\n"
            f"• {', '.join(self.scraper_factory.get_supported_websites())}"
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_message = (
            "🤖 HouseHunter Bot Help\n\n"
            "📝 How to use:\n"
            "1. Send me a property URL from a supported website\n"
            "2. I'll scrape the property details automatically\n"
            "3. The property will be saved to your Notion database\n\n"
            "🌐 Supported websites:\n"
            f"• {', '.join(self.scraper_factory.get_supported_websites())}\n\n"
            "⚡ Commands:\n"
            "/start - Welcome message\n"
            "/help - This help message\n"
            "/status - Check if everything is working\n"
            "/supported - List all supported websites\n\n"
            "❓ Need more help? Check the project documentation!"
        )
        await update.message.reply_text(help_message)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            # Check Notion database connection
            notion_status = await self.notion_service.check_database_exists()
            
            if notion_status:
                db_info = await self.notion_service.get_database_info()
                status_message = (
                    "✅ Bot Status: Running\n"
                    "✅ Notion Database: Connected\n"
                    f"📊 Database: {db_info.get('database_title', 'Unknown')}\n"
                    f"🔧 Available scrapers: {len(self.scraper_factory.scrapers)}\n"
                    f"🌐 Supported sites: {', '.join(self.scraper_factory.get_supported_websites())}"
                )
            else:
                status_message = (
                    "✅ Bot Status: Running\n"
                    "❌ Notion Database: Connection failed\n"
                    "Please check your Notion configuration."
                )
            
        except Exception as e:
            status_message = (
                "✅ Bot Status: Running\n"
                f"❌ Error checking status: {str(e)}"
            )
        
        await update.message.reply_text(status_message)
    
    async def supported_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /supported command"""
        supported_sites = self.scraper_factory.get_supported_websites()
        
        message = (
            "🌐 Supported Property Websites:\n\n"
            + "\n".join([f"• {site}" for site in supported_sites])
            + f"\n\nTotal: {len(supported_sites)} website(s) supported"
        )
        
        await update.message.reply_text(message)
    
    async def predictions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /predictions command - show detailed prediction times for a property"""
        # Check if this is a reply to a property message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "📋 **Usage**: Reply to a property message with `/predictions` to see detailed travel times.\n\n"
                "This command shows comprehensive route information including:\n"
                "• Detailed route breakdowns\n"
                "• Walking segments\n"
                "• Transit line information\n"
                "• Alternative routes"
            )
            return
        
        # Check if the replied message contains property information
        replied_text = update.message.reply_to_message.text
        if "Property saved successfully" not in replied_text:
            await update.message.reply_text(
                "❌ Please reply to a property message (one that shows 'Property saved successfully') to see detailed predictions."
            )
            return
        
        # Extract the property URL from the replied message
        url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', replied_text)
        if not url_match:
            await update.message.reply_text(
                "❌ Could not find the property URL in the replied message."
            )
            return
        
        property_url = url_match.group(0)
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔄 Calculating detailed prediction times..."
        )
        
        try:
            # Get the property from the database
            property_data = await self.property_service.get_property_by_url(property_url)
            if not property_data:
                await processing_msg.edit_text(
                    "❌ Property not found in database. Please try processing the property URL again."
                )
                return
            
            # Check if property has coordinates
            if not (hasattr(property_data, 'address') and 
                   hasattr(property_data.address, 'latitude') and 
                   hasattr(property_data.address, 'longitude') and
                   property_data.address.latitude is not None and 
                   property_data.address.longitude is not None):
                await processing_msg.edit_text(
                    "❌ Property coordinates not available. Cannot calculate travel times."
                )
                return
            
            # Calculate predictions
            property_address = f"{property_data.address.city}, {property_data.address.county or ''}"
            prediction_info = await self.interest_points_service.calculate_predictions_for_property(
                property_data.address.latitude,
                property_data.address.longitude,
                property_address
            )
            
            if not prediction_info or not prediction_info.predictions:
                await processing_msg.edit_text(
                    "❌ No prediction data available for this property."
                )
                return
            
            # Build detailed message
            detailed_message = (
                f"🚗 **Detailed Travel Times for Next Friday 9am**\n"
                f"📍 **Property**: {property_data.address.city}, {property_data.address.county or ''}\n\n"
            )
            
            for i, prediction in enumerate(prediction_info.predictions, 1):
                point_name = prediction.destination_point_id
                interest_point = self.interest_points_service.get_interest_point_by_id(prediction.destination_point_id)
                if interest_point:
                    point_name = interest_point.name
                
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
                
                transport_emoji = transport_emojis.get(prediction.transportation_mode.value.upper(), "🚗")
                distance_display = f"{prediction.distance_km:.1f}km" if prediction.distance_km >= 1.0 else f"{prediction.distance_km:.3f}km"
                
                detailed_message += (
                    f"**{i}. {transport_emoji} {point_name}**\n"
                    f"⏱️ {prediction.duration_minutes}min • 📏 {distance_display}\n"
                    f"🕐 Depart: {prediction.departure_time} • Arrive: {prediction.arrival_time}\n\n"
                )
                
                # Add detailed route breakdown
                if prediction.route_details and len(prediction.route_details) > 0:
                    detailed_message += "**Route Details:**\n"
                    
                    for j, section in enumerate(prediction.route_details, 1):
                        section_type = section.get("type", "unknown")
                        duration = section.get("duration_minutes", 0)
                        distance_m = section.get("distance_m", 0)
                        
                        if section_type == "transit":
                            mode = section.get("mode", "unknown")
                            name = section.get("name", "Unknown")
                            line = section.get("line", "")
                            
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
                                detailed_message += f"  {j}. {mode_emoji} **{line}** ({duration}min, {distance_display})\n"
                            else:
                                detailed_message += f"  {j}. {mode_emoji} **{name}** ({duration}min, {distance_display})\n"
                                
                        elif section_type == "pedestrian":
                            distance_km = distance_m / 1000
                            distance_display = f"{distance_km:.1f}km" if distance_km >= 1.0 else f"{distance_km:.3f}km"
                            detailed_message += f"  {j}. 🚶 **Walking** ({duration}min, {distance_display})\n"
                            
                        else:
                            detailed_message += f"  {j}. **{section_type.title()}** ({duration}min)\n"
                    
                    # Add summary
                    num_legs = len(prediction.route_details)
                    total_walking = sum(s.get("duration_minutes", 0) for s in prediction.route_details if s.get("type") == "pedestrian")
                    total_transit = sum(s.get("duration_minutes", 0) for s in prediction.route_details if s.get("type") == "transit")
                    
                    walking_legs = sum(1 for s in prediction.route_details if s.get("type") == "pedestrian")
                    transit_legs = sum(1 for s in prediction.route_details if s.get("type") == "transit")
                    
                    summary_parts = []
                    if transit_legs > 0:
                        summary_parts.append(f"🚌 {transit_legs} transit")
                    if walking_legs > 0:
                        summary_parts.append(f"🚶 {walking_legs} walking")
                    
                    detailed_message += f"📊 **Summary**: {num_legs} legs • {' + '.join(summary_parts)}\n"
                    detailed_message += f"⏱️ **Total**: {total_transit}min transit + {total_walking}min walking\n\n"
                
                detailed_message += "─" * 40 + "\n\n"
            
            # Check if message is too long and split if necessary
            if len(detailed_message) > 4000:
                parts = self._split_message(detailed_message)
                
                # Edit the first part into the processing message
                try:
                    await processing_msg.edit_text(parts[0], parse_mode='Markdown')
                except Exception as e:
                    logger.warning(f"Failed to edit first detailed message part: {e}")
                    await update.message.reply_text(parts[0], parse_mode='Markdown')
                
                # Send remaining parts as new messages
                for part in parts[1:]:
                    try:
                        await update.message.reply_text(part, parse_mode='Markdown')
                    except Exception as e:
                        logger.warning(f"Failed to send detailed message part: {e}")
                        try:
                            await update.message.reply_text(part)
                        except Exception as e2:
                            logger.error(f"Failed to send detailed message part without parse_mode: {e2}")
            else:
                await processing_msg.edit_text(detailed_message, parse_mode='Markdown')
                
        except Exception as e:
            await processing_msg.edit_text(
                f"❌ Error calculating detailed predictions: {str(e)}"
            )
            logger.error(f"Error in predictions command: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages"""
        message_text = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Check if this is a group chat
        chat_type = update.effective_chat.type
        is_group_chat = chat_type in ['group', 'supergroup']
        
        logger.info(f"Received message from user {username} ({user_id}) in {chat_type}: {message_text}")
        
        # Check if message contains URLs
        if not self._is_url(message_text):
            # Add username prefix for group chats
            username_prefix = f"👤 @{username}: " if is_group_chat else ""
            
            await update.message.reply_text(
                f"{username_prefix}🤔 I don't see any URLs in your message.\n\n"
                "Please send me a property URL from a supported website, or use /help for more information."
            )
            return
        
        # Extract URLs from message
        urls = self._extract_urls(message_text)
        
        if not urls:
            # Add username prefix for group chats
            username_prefix = f"👤 @{username}: " if is_group_chat else ""
            
            await update.message.reply_text(
                f"{username_prefix}🤔 I couldn't extract any valid URLs from your message.\n\n"
                "Please make sure the URL is complete and try again."
            )
            return
        
        # Process each URL
        if len(urls) == 1:
            # Single URL - process directly
            await self._process_property_url(update, urls[0], username)
        else:
            # Multiple URLs - send a summary and process each one
            username_prefix = f"👤 @{username}: " if is_group_chat else ""
            
            summary_msg = await update.message.reply_text(
                f"{username_prefix}🔗 Found {len(urls)} URLs in your message. Processing each one..."
            )
            
            for i, url_str in enumerate(urls, 1):
                await summary_msg.edit_text(
                    f"🔗 Processing URL {i}/{len(urls)}...\n📍 {url_str}"
                )
                await self._process_property_url(update, url_str, username)
            
            # Final summary
            await summary_msg.edit_text(
                f"{username_prefix}✅ Finished processing {len(urls)} URLs from your message!"
            )
    
    async def _process_property_url(self, update: Update, url_str: str, username: str) -> None:
        """Process a single property URL"""
        try:
            # Validate URL
            try:
                url = HttpUrl(url_str)
            except ValidationError:
                username_prefix = f"👤 @{username}: " if update.effective_chat.type in ['group', 'supergroup'] else ""
                await update.message.reply_text(f"{username_prefix}❌ Invalid URL format: {url_str}")
                return
            
            # Send initial processing message as a reply to the original message
            processing_msg = await update.message.reply_text(
                f"🔄 Processing property URL...\n📍 {url_str}"
            )
            
            # Check if scraper exists for this URL
            scraper = self.scraper_factory.get_scraper_for_url(url)
            if not scraper:
                supported_sites = self.scraper_factory.get_supported_websites()
                username_prefix = f"👤 @{username}: " if update.effective_chat.type in ['group', 'supergroup'] else ""
                await processing_msg.edit_text(
                    f"{username_prefix}❌ Unsupported website\n\n"
                    f"🌐 Supported sites: {', '.join(supported_sites)}"
                )
                return
            
            # Scrape the property
            await processing_msg.edit_text(
                f"🔄 Scraping property data...\n📍 {url_str}"
            )
            
            property_data = await self.scraper_factory.scrape_property(url)
            if not property_data:
                username_prefix = f"👤 @{username}: " if update.effective_chat.type in ['group', 'supergroup'] else ""
                await processing_msg.edit_text(
                    f"{username_prefix}❌ Failed to scrape property data\n📍 {url_str}\n\n"
                    "The property page might be unavailable or the structure has changed."
                )
                return
            
            # Save to property service
            await processing_msg.edit_text(
                f"💾 Saving property data...\n📍 {url_str}"
            )
            
            saved_property = await self.property_service.create_property(property_data)
            
            # Calculate prediction times for next Friday at 9am BEFORE saving to Notion
            await processing_msg.edit_text(
                f"🚗 Calculating prediction times for next Friday 9am...\n📍 {url_str}"
            )
            
            prediction_info = None
            try:
                # Check if property has coordinates
                has_coordinates = False
                latitude = None
                longitude = None
                
                logger.info(f"Checking coordinates for property: {property_data.address if hasattr(property_data, 'address') else 'No address'}")
                
                if (hasattr(property_data, 'address') and 
                    hasattr(property_data.address, 'latitude') and 
                    hasattr(property_data.address, 'longitude') and
                    property_data.address.latitude is not None and 
                    property_data.address.longitude is not None):
                    has_coordinates = True
                    latitude = property_data.address.latitude
                    longitude = property_data.address.longitude
                    logger.info(f"Property has coordinates from scraper: {latitude}, {longitude}")
                else:
                    logger.info("Property coordinates not available from scraper, attempting geocoding...")
                    
                    # Try geocoding as fallback
                    if hasattr(property_data, 'address') and property_data.address:
                        geocoded_coords = await self.geocoding_service.geocode_property_address(property_data.address)
                        if geocoded_coords:
                            has_coordinates = True
                            latitude, longitude = geocoded_coords
                            logger.info(f"Property coordinates obtained via geocoding: {latitude}, {longitude}")
                            
                            # Update the property address with the geocoded coordinates
                            property_data.address.latitude = latitude
                            property_data.address.longitude = longitude
                        else:
                            logger.warning("Geocoding failed, no coordinates available")
                    else:
                        logger.warning("No address object available for geocoding")
                
                if has_coordinates and latitude is not None and longitude is not None:
                    property_address = f"{property_data.address.city}, {property_data.address.county or ''}"
                    prediction_info = await self.interest_points_service.calculate_predictions_for_property(
                        latitude,
                        longitude,
                        property_address
                    )
                    logger.info(f"Prediction info calculated: {len(prediction_info.predictions) if prediction_info else 0} predictions")
                else:
                    logger.info("No coordinates available, skipping prediction times")
                    
            except Exception as e:
                logger.warning(f"Failed to calculate prediction times: {e}")
                import traceback
                logger.warning(f"Traceback: {traceback.format_exc()}")
            
            # Save to Notion (pass predictions so the Transportation section is included)
            await processing_msg.edit_text(
                f"📝 Saving to Notion database...\n📍 {url_str}"
            )
            
            notion_result = await self.notion_service.save_property_to_notion(saved_property, prediction_info)
            
            # Send success/failure message
            if notion_result.get("success"):
                # Add username prefix for group chats
                username_prefix = f"👤 @{username}: " if update.effective_chat.type in ['group', 'supergroup'] else ""
                
                # Build concise success message
                success_message = (
                    f"{username_prefix}✅ Property saved successfully!\n\n"
                    f"🏠 {property_data.property_type.value.title()}\n"
                    f"📍 {property_data.address.city}, {property_data.address.county or ''}\n"
                    f"🛏️ {property_data.bedrooms} bed, {property_data.bathrooms} bath\n"
                    f"📐 {property_data.area_sqm}m²\n"
                    f"💰 {property_data.primary_listing.price if property_data.primary_listing else 'N/A'}\n\n"
                )
                
                # Add prediction times if available
                if prediction_info and prediction_info.predictions and len(prediction_info.predictions) > 0:
                    success_message += f"🚗 **Next Friday 9am Predictions:**\n"
                    
                    # Show all predictions to display all interest points
                    for i, prediction in enumerate(prediction_info.predictions):
                        point_name = prediction.destination_point_id
                        # Try to get the actual point name
                        interest_point = self.interest_points_service.get_interest_point_by_id(prediction.destination_point_id)
                        if interest_point:
                            point_name = interest_point.name
                        
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
                        
                        # Get the appropriate emoji for the transportation mode
                        transport_emoji = transport_emojis.get(prediction.transportation_mode.value.upper(), "🚗")
                        
                        # For public transport, use a more specific emoji based on the route details
                        if prediction.transportation_mode.value == "publicTransport" and prediction.route_details:
                            # Check if we have transit sections to determine the primary mode
                            transit_sections = [s for s in prediction.route_details if s.get("type") == "transit"]
                            if transit_sections:
                                primary_mode = transit_sections[0].get("mode", "bus")
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
                                transport_emoji = mode_emojis.get(primary_mode, "🚌")
                        
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
                        
                        success_message += (
                            f"• {transport_emoji} **{point_name}**: "
                            f"{prediction.duration_minutes}min ({distance_display}){walking_info}\n"
                            f"  Depart: {prediction.departure_time} • Arrive: {prediction.arrival_time}\n"
                        )
                    

                    
                    success_message += "\n"
                
                elif not has_coordinates:
                    success_message += "⚠️ *Prediction times not available* - Property coordinates not found\n\n"
                else:
                    # Coordinates are available but predictions failed or are empty
                    success_message += "⚠️ *Prediction times not available* - Unable to calculate travel times (HERE API error)\n\n"
                
                success_message += (
                    f"📋 [View in Notion]({notion_result.get('notion_page_url', '#')})\n"
                    f"🔗 [Original listing]({url_str})"
                )
                
                # Check if message is too long and split if necessary
                if len(success_message) > 4000:
                    # Split the message and send as multiple messages
                    parts = self._split_message(success_message)
                    
                    # Edit the first part into the existing processing message
                    try:
                        await processing_msg.edit_text(parts[0], parse_mode='Markdown')
                    except Exception as e:
                        logger.warning(f"Failed to edit first message part: {e}")
                        # If editing fails, send as new message
                        await update.message.reply_text(parts[0], parse_mode='Markdown')
                    
                    # Send remaining parts as new messages
                    for part in parts[1:]:
                        try:
                            await update.message.reply_text(part, parse_mode='Markdown')
                        except Exception as e:
                            logger.warning(f"Failed to send message part: {e}")
                            # Try without parse_mode if it fails
                            try:
                                await update.message.reply_text(part)
                            except Exception as e2:
                                logger.error(f"Failed to send message part without parse_mode: {e2}")
                else:
                    # Message is short enough, just edit the existing message
                    await processing_msg.edit_text(success_message, parse_mode='Markdown')
                
                logger.info(f"Successfully processed property for user {username}: {url_str}")
            else:
                # Add username prefix for group chats
                username_prefix = f"👤 @{username}: " if update.effective_chat.type in ['group', 'supergroup'] else ""
                
                error_message = (
                    f"{username_prefix}⚠️ Property scraped but failed to save to Notion\n\n"
                    f"🏠 {property_data.property_type.value.title()}\n"
                    f"📍 {property_data.address.city}\n\n"
                    f"❌ Notion error: {notion_result.get('error', 'Unknown error')}\n"
                    f"🔗 [Original listing]({url_str})"
                )
                # Check if error message is too long and split if necessary
                if len(error_message) > 4000:
                    parts = self._split_message(error_message)
                    
                    # Edit the first part into the existing processing message
                    try:
                        await processing_msg.edit_text(parts[0], parse_mode='Markdown')
                    except Exception as e:
                        logger.warning(f"Failed to edit first error message part: {e}")
                        await update.message.reply_text(parts[0], parse_mode='Markdown')
                    
                    # Send remaining parts as new messages
                    for part in parts[1:]:
                        try:
                            await update.message.reply_text(part, parse_mode='Markdown')
                        except Exception as e:
                            logger.warning(f"Failed to send error message part: {e}")
                            try:
                                await update.message.reply_text(part)
                            except Exception as e2:
                                logger.error(f"Failed to send error message part without parse_mode: {e2}")
                else:
                    await processing_msg.edit_text(error_message, parse_mode='Markdown')
                
                logger.error(f"Failed to save to Notion for user {username}: {notion_result.get('error')}")
                
        except Exception as e:
            username_prefix = f"👤 @{username}: " if update.effective_chat.type in ['group', 'supergroup'] else ""
            error_message = (
                f"{username_prefix}❌ Error processing property\n📍 {url_str}\n\n"
                f"Error: {str(e)}"
            )
            try:
                await processing_msg.edit_text(error_message)
            except:
                await update.message.reply_text(error_message)
            
            logger.error(f"Error processing property for user {username}: {str(e)}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if isinstance(update, Update) and update.message:
            await update.message.reply_text(
                "😞 Sorry, something went wrong. Please try again later."
            )
    
    def setup_handlers(self) -> None:
        """Set up message and command handlers"""
        if not self.application:
            return
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("supported", self.supported_command))
        self.application.add_handler(CommandHandler("predictions", self.predictions_command))
        
        # Message handler for URLs
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_bot(self) -> None:
        """Start the Telegram bot"""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        try:
            # Create application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Setup handlers
            self.setup_handlers()
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.is_running = True
            logger.info("Telegram bot started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {str(e)}")
            raise
    
    async def stop_bot(self) -> None:
        """Stop the Telegram bot"""
        if not self.is_running or not self.application:
            logger.warning("Bot is not running")
            return
        
        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            self.is_running = False
            logger.info("Telegram bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {str(e)}")
            raise
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        return {
            "is_running": self.is_running,
            "bot_token_configured": bool(self.bot_token),
            "notion_configured": bool(self.notion_service.notion_token and self.notion_service.database_id),
            "supported_websites": self.scraper_factory.get_supported_websites(),
            "scraper_count": len(self.scraper_factory.scrapers)
        } 