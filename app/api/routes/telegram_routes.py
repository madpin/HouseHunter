from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any

from app.services.telegram_service import TelegramService
from app.services.notion_service import NotionService
from app.services.property_service import PropertyService
from app.scrapers.scraper_factory import ScraperFactory
from app.config import config

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Global telegram service instance
_telegram_service: TelegramService = None

def get_telegram_service() -> TelegramService:
    """Get or create Telegram service instance"""
    global _telegram_service
    
    if not config.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="Telegram bot token not configured. Set TELEGRAM_BOT_TOKEN environment variable."
        )
    
    if _telegram_service is None:
        try:
            _telegram_service = TelegramService(
                bot_token=config.TELEGRAM_BOT_TOKEN,
                notion_service=NotionService(),
                property_service=PropertyService(),
                scraper_factory=ScraperFactory()
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return _telegram_service

@router.get("/status")
async def get_telegram_bot_status(
    telegram_service: TelegramService = Depends(get_telegram_service)
) -> Dict[str, Any]:
    """
    Get Telegram bot status and configuration
    """
    try:
        bot_info = telegram_service.get_bot_info()
        
        return {
            "bot_configured": bool(config.TELEGRAM_BOT_TOKEN),
            "bot_enabled": config.TELEGRAM_BOT_ENABLED,
            "bot_running": bot_info["is_running"],
            "notion_configured": bot_info["notion_configured"],
            "supported_websites": bot_info["supported_websites"],
            "scraper_count": bot_info["scraper_count"],
            "message": "Bot status retrieved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bot status: {str(e)}")

@router.post("/start")
async def start_telegram_bot(
    background_tasks: BackgroundTasks,
    telegram_service: TelegramService = Depends(get_telegram_service)
) -> Dict[str, Any]:
    """
    Start the Telegram bot
    """
    try:
        if telegram_service.is_running:
            return {
                "success": True,
                "message": "Telegram bot is already running"
            }
        
        # Start bot in background
        background_tasks.add_task(telegram_service.start_bot)
        
        return {
            "success": True,
            "message": "Telegram bot start initiated. Check status for updates."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting bot: {str(e)}")

@router.post("/stop")
async def stop_telegram_bot(
    background_tasks: BackgroundTasks,
    telegram_service: TelegramService = Depends(get_telegram_service)
) -> Dict[str, Any]:
    """
    Stop the Telegram bot
    """
    try:
        if not telegram_service.is_running:
            return {
                "success": True,
                "message": "Telegram bot is not running"
            }
        
        # Stop bot in background
        background_tasks.add_task(telegram_service.stop_bot)
        
        return {
            "success": True,
            "message": "Telegram bot stop initiated. Check status for updates."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping bot: {str(e)}")

@router.post("/restart")
async def restart_telegram_bot(
    background_tasks: BackgroundTasks,
    telegram_service: TelegramService = Depends(get_telegram_service)
) -> Dict[str, Any]:
    """
    Restart the Telegram bot
    """
    try:
        # Stop if running
        if telegram_service.is_running:
            await telegram_service.stop_bot()
        
        # Start bot in background
        background_tasks.add_task(telegram_service.start_bot)
        
        return {
            "success": True,
            "message": "Telegram bot restart initiated. Check status for updates."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restarting bot: {str(e)}")

@router.get("/config")
async def get_telegram_config() -> Dict[str, Any]:
    """
    Get Telegram bot configuration (without sensitive data)
    """
    return {
        "bot_token_configured": bool(config.TELEGRAM_BOT_TOKEN),
        "bot_enabled": config.TELEGRAM_BOT_ENABLED,
        "notion_token_configured": bool(config.NOTION_TOKEN),
        "notion_database_configured": bool(config.NOTION_DATABASE_ID),
        "supported_websites": ScraperFactory().get_supported_websites(),
        "message": "Configuration retrieved successfully"
    } 