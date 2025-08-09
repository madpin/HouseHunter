#!/usr/bin/env python3
"""
Test script to verify telegram service predictions are working
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.telegram_service import TelegramService
from app.services.interest_points_service import InterestPointsService

# Load environment variables
load_dotenv()

async def test_telegram_predictions():
    """Test that telegram service can calculate predictions"""
    
    # Initialize services
    interest_points_service = InterestPointsService("config/interest_points_config.json")
    telegram_service = TelegramService()
    
    # Test coordinates (Dublin city center)
    test_coordinates = {
        "latitude": 53.3498,
        "longitude": -6.2603
    }
    
    print("🔍 Testing Telegram Service Predictions...")
    print("=" * 50)
    
    # Test interest points loading
    try:
        points = interest_points_service.get_active_interest_points()
        print(f"✅ Loaded {len(points)} active interest points")
        
        # Test prediction calculation
        predictions = await interest_points_service.calculate_predictions_for_property(
            test_coordinates["latitude"],
            test_coordinates["longitude"],
            "Test Property Address"
        )
        
        if predictions and predictions.predictions:
            print(f"✅ Successfully calculated {len(predictions.predictions)} predictions")
            for pred in predictions.predictions:
                # Get the point name from the destination_point_id
                point = interest_points_service.get_interest_point_by_id(pred.destination_point_id)
                point_name = point.name if point else pred.destination_point_id
                print(f"   - {point_name}: {pred.duration_minutes} min")
        else:
            print("❌ No predictions returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_telegram_predictions())
