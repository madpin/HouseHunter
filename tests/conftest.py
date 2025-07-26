"""
Pytest configuration for HouseHunter API tests
"""

import pytest
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

@pytest.fixture
def test_env():
    """Fixture to set up test environment variables"""
    # Set test environment variables
    os.environ["NOTION_TOKEN"] = "test_token"
    os.environ["NOTION_DATABASE_ID"] = "test_database_id"
    yield
    # Clean up
    os.environ.pop("NOTION_TOKEN", None)
    os.environ.pop("NOTION_DATABASE_ID", None) 