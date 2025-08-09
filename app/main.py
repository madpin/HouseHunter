from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import property_routes, notion_routes, telegram_routes, interest_points_routes
from app.config import config
from app.services.telegram_service import TelegramService
import asyncio
import logging

# Create FastAPI app
app = FastAPI(
    title="HouseHunter API",
    description="A comprehensive property management API that supports multiple listing websites",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(property_routes.router)
app.include_router(notion_routes.router)
app.include_router(telegram_routes.router)
app.include_router(interest_points_routes.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to HouseHunter API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logging.info("Starting HouseHunter API...")
    
    # Auto-start Telegram bot if enabled
    if config.TELEGRAM_BOT_ENABLED and config.TELEGRAM_BOT_TOKEN:
        try:
            logging.info("Auto-starting Telegram bot...")
            telegram_service = TelegramService()
            asyncio.create_task(telegram_service.start_bot())
        except Exception as e:
            logging.error(f"Failed to auto-start Telegram bot: {str(e)}")
    
    logging.info("HouseHunter API startup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=config.API_HOST, 
        port=config.API_PORT,
        debug=config.DEBUG
    ) 