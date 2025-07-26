import pytest
import os
from unittest.mock import Mock, patch
from app.services.telegram_service import TelegramService
from app.services.notion_service import NotionService
from app.services.property_service import PropertyService
from app.scrapers.scraper_factory import ScraperFactory

class TestTelegramService:
    """Test cases for TelegramService"""
    
    def test_telegram_service_initialization_with_token(self):
        """Test TelegramService initialization with provided token"""
        mock_notion_service = Mock(spec=NotionService)
        mock_property_service = Mock(spec=PropertyService)
        mock_scraper_factory = Mock(spec=ScraperFactory)
        
        service = TelegramService(
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            notion_service=mock_notion_service,
            property_service=mock_property_service,
            scraper_factory=mock_scraper_factory
        )
        
        assert service.bot_token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        assert service.notion_service == mock_notion_service
        assert service.property_service == mock_property_service
        assert service.scraper_factory == mock_scraper_factory
        assert not service.is_running
        assert service.application is None
    
    def test_telegram_service_initialization_without_token_raises_error(self):
        """Test TelegramService initialization without token raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Telegram bot token is required"):
                TelegramService()
    
    @patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})
    def test_telegram_service_initialization_with_env_token(self):
        """Test TelegramService initialization using environment variable"""
        service = TelegramService()
        assert service.bot_token == "test_token"
        assert isinstance(service.notion_service, NotionService)
        assert isinstance(service.property_service, PropertyService)
        assert isinstance(service.scraper_factory, ScraperFactory)
    
    def test_is_url_detection(self):
        """Test URL detection functionality"""
        service = TelegramService(bot_token="test_token")
        
        # Valid URLs
        assert service._is_url("https://www.daft.ie/property/123")
        assert service._is_url("http://example.com/page")
        assert service._is_url("Check this out: https://www.daft.ie/property/123")
        assert service._is_url("https://www.daft.ie/for-sale/house-18-rosan-glas-rahoon-co-galway/6231936")
        
        # Invalid URLs
        assert not service._is_url("Just some text")
        assert not service._is_url("www.example.com")  # No protocol
        assert not service._is_url("not a url at all")
    
    def test_extract_urls(self):
        """Test URL extraction from text"""
        service = TelegramService(bot_token="test_token")
        
        text = "Check out this property: https://www.daft.ie/property/123 and also this one http://example.com/test"
        urls = service._extract_urls(text)
        
        assert len(urls) == 2
        assert "https://www.daft.ie/property/123" in urls
        assert "http://example.com/test" in urls
        
        # Test with the specific Daft URL that was failing
        daft_text = "https://www.daft.ie/for-sale/house-18-rosan-glas-rahoon-co-galway/6231936"
        daft_urls = service._extract_urls(daft_text)
        
        assert len(daft_urls) == 1
        assert "https://www.daft.ie/for-sale/house-18-rosan-glas-rahoon-co-galway/6231936" in daft_urls
    
    def test_get_bot_info(self):
        """Test get_bot_info method"""
        mock_notion_service = Mock()
        mock_notion_service.notion_token = "test_notion_token"
        mock_notion_service.database_id = "test_database_id"
        
        mock_scraper_factory = Mock()
        mock_scraper_factory.get_supported_websites.return_value = ["daft.ie"]
        mock_scraper_factory.scrapers = [Mock()]
        
        service = TelegramService(
            bot_token="test_token",
            notion_service=mock_notion_service,
            scraper_factory=mock_scraper_factory
        )
        
        bot_info = service.get_bot_info()
        
        assert bot_info["is_running"] is False
        assert bot_info["bot_token_configured"] is True
        assert bot_info["notion_configured"] is True
        assert bot_info["supported_websites"] == ["daft.ie"]
        assert bot_info["scraper_count"] == 1

@pytest.mark.asyncio
class TestTelegramServiceAsync:
    """Async test cases for TelegramService"""
    
    async def test_start_bot_updates_running_status(self):
        """Test that start_bot method properly updates running status"""
        service = TelegramService(bot_token="test_token")
        
        # Mock the application setup to avoid actual Telegram API calls
        with patch.object(service, 'application', None):
            with patch('app.services.telegram_service.Application') as mock_app_class:
                mock_app = Mock()
                mock_app_class.builder.return_value.token.return_value.build.return_value = mock_app
                
                # Mock async methods
                mock_app.initialize = Mock(return_value=None)
                mock_app.start = Mock(return_value=None)
                mock_app.updater.start_polling = Mock(return_value=None)
                
                await service.start_bot()
                
                assert service.is_running is True
    
    async def test_stop_bot_updates_running_status(self):
        """Test that stop_bot method properly updates running status"""
        service = TelegramService(bot_token="test_token")
        service.is_running = True
        
        # Mock the application
        mock_app = Mock()
        mock_app.updater.stop = Mock(return_value=None)
        mock_app.stop = Mock(return_value=None)
        mock_app.shutdown = Mock(return_value=None)
        service.application = mock_app
        
        await service.stop_bot()
        
        assert service.is_running is False 
    
    async def test_group_chat_message_handling(self):
        """Test that bot properly handles messages in group chats with username prefixes"""
        service = TelegramService(bot_token="test_token")
        
        # Create a mock update with group chat context
        mock_update = Mock()
        mock_update.message.text = "https://www.daft.ie/property/123"
        mock_update.effective_user.id = 12345
        mock_update.effective_user.username = "testuser"
        mock_update.effective_user.first_name = "Test"
        mock_update.effective_chat.type = "group"
        
        # Mock the message reply method
        mock_message = Mock()
        mock_update.message.reply_text = Mock(return_value=mock_message)
        mock_message.edit_text = Mock(return_value=None)
        
        # Mock the URL processing to avoid actual scraping
        with patch.object(service, '_process_property_url') as mock_process:
            await service.handle_message(mock_update, Mock())
            
            # Verify that the message was processed
            mock_process.assert_called_once()
            
            # Verify that the first call includes the update, URL, and username
            call_args = mock_process.call_args[0]
            assert call_args[0] == mock_update
            assert call_args[1] == "https://www.daft.ie/property/123"
            assert call_args[2] == "testuser" 
    
    async def test_private_chat_message_handling(self):
        """Test that bot properly handles messages in private chats without username prefixes"""
        service = TelegramService(bot_token="test_token")
        
        # Create a mock update with private chat context
        mock_update = Mock()
        mock_update.message.text = "https://www.daft.ie/property/123"
        mock_update.effective_user.id = 12345
        mock_update.effective_user.username = "testuser"
        mock_update.effective_user.first_name = "Test"
        mock_update.effective_chat.type = "private"
        
        # Mock the message reply method
        mock_message = Mock()
        mock_update.message.reply_text = Mock(return_value=mock_message)
        mock_message.edit_text = Mock(return_value=None)
        
        # Mock the URL processing to avoid actual scraping
        with patch.object(service, '_process_property_url') as mock_process:
            await service.handle_message(mock_update, Mock())
            
            # Verify that the message was processed
            mock_process.assert_called_once()
            
            # Verify that the first call includes the update, URL, and username
            call_args = mock_process.call_args[0]
            assert call_args[0] == mock_update
            assert call_args[1] == "https://www.daft.ie/property/123"
            assert call_args[2] == "testuser" 