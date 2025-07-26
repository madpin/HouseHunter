import logging
import re
from typing import Optional, Dict, Any
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pydantic import HttpUrl, ValidationError

from app.config import config
from app.services.notion_service import NotionService
from app.services.property_service import PropertyService
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
                 scraper_factory: Optional[ScraperFactory] = None):
        """
        Initialize Telegram service
        
        Args:
            bot_token: Telegram bot token (defaults to TELEGRAM_BOT_TOKEN env var)
            notion_service: NotionService instance
            property_service: PropertyService instance  
            scraper_factory: ScraperFactory instance
        """
        self.bot_token = bot_token or config.TELEGRAM_BOT_TOKEN
        if not self.bot_token:
            raise ValueError("Telegram bot token is required. Set TELEGRAM_BOT_TOKEN environment variable.")
        
        self.notion_service = notion_service or NotionService()
        self.property_service = property_service or PropertyService()
        self.scraper_factory = scraper_factory or ScraperFactory()
        
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
            
            # Save to Notion
            await processing_msg.edit_text(
                f"📝 Saving to Notion database...\n📍 {url_str}"
            )
            
            notion_result = await self.notion_service.save_property_to_notion(saved_property)
            
            # Send success/failure message
            if notion_result.get("success"):
                # Add username prefix for group chats
                username_prefix = f"👤 @{username}: " if update.effective_chat.type in ['group', 'supergroup'] else ""
                
                success_message = (
                    f"{username_prefix}✅ Property saved successfully!\n\n"
                    f"🏠 {property_data.property_type.value.title()}\n"
                    f"📍 {property_data.address.city}, {property_data.address.county or ''}\n"
                    f"🛏️ {property_data.bedrooms} bed, {property_data.bathrooms} bath\n"
                    f"📐 {property_data.area_sqm}m²\n"
                    f"💰 {property_data.primary_listing.price if property_data.primary_listing else 'N/A'}\n\n"
                    f"📋 [View in Notion]({notion_result.get('notion_page_url', '#')})\n"
                    f"🔗 [Original listing]({url_str})"
                )
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