import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Notion Integration
    NOTION_TOKEN: Optional[str] = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID: Optional[str] = os.getenv("NOTION_DATABASE_ID")
    
    # Database Configuration (for future use)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Security (for future use)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-change-this-in-production")
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_BOT_ENABLED: bool = os.getenv("TELEGRAM_BOT_ENABLED", "false").lower() == "true"
    
    # External APIs (for future use)
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # HERE API Configuration
    HERE_API_KEY: Optional[str] = os.getenv("HERE_API_KEY")
    HERE_API_ENABLED: bool = os.getenv("HERE_API_ENABLED", "false").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate_notion_config(cls) -> bool:
        """Validate that Notion configuration is complete"""
        return bool(cls.NOTION_TOKEN and cls.NOTION_DATABASE_ID)
    
    @classmethod
    def get_notion_config(cls) -> tuple[str, str]:
        """Get Notion configuration as tuple (token, database_id)"""
        if not cls.validate_notion_config():
            raise ValueError(
                "Notion configuration incomplete. "
                "Set NOTION_TOKEN and NOTION_DATABASE_ID environment variables."
            )
        return cls.NOTION_TOKEN, cls.NOTION_DATABASE_ID
    
    @classmethod
    def validate_here_api_config(cls) -> bool:
        """Validate that HERE API configuration is complete"""
        return bool(cls.HERE_API_KEY and cls.HERE_API_ENABLED)
    
    @classmethod
    def get_here_api_config(cls) -> str:
        """Get HERE API configuration as string (api_key)"""
        if not cls.validate_here_api_config():
            raise ValueError(
                "HERE API configuration incomplete. "
                "Set HERE_API_KEY and HERE_API_ENABLED=true environment variables."
            )
        return cls.HERE_API_KEY

# Global config instance
config = Config() 