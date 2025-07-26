#!/usr/bin/env python3
"""
Environment setup script for HouseHunter API
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up the environment configuration"""
    
    print("🏠 HouseHunter API Environment Setup")
    print("=" * 50)
    
    # Check if .env file already exists
    env_file = Path(".env")
    example_file = Path("env.example")
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Copy example file
    if example_file.exists():
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from env.example")
    else:
        print("❌ env.example file not found!")
        return
    
    # Get user input for Notion configuration
    print("\n🔧 Notion Integration Setup")
    print("Get your Notion integration token from: https://www.notion.so/my-integrations")
    
    notion_token = input("Enter your Notion integration token: ").strip()
    notion_db_id = input("Enter your Notion database ID: ").strip()
    
    # Update .env file
    if notion_token and notion_db_id:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace placeholder values
        content = content.replace("your_notion_integration_token_here", notion_token)
        content = content.replace("your_notion_database_id_here", notion_db_id)
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Notion configuration saved to .env file")
    else:
        print("⚠️  Notion configuration not provided. You'll need to edit .env manually.")
    
    # Optional: Get other configurations
    print("\n🔧 Optional Configurations")
    
    api_port = input("API Port (default: 8000): ").strip()
    if api_port:
        with open(env_file, 'r') as f:
            content = f.read()
        content = content.replace("API_PORT=8000", f"API_PORT={api_port}")
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ API port configuration saved")
    
    debug_mode = input("Enable debug mode? (y/N): ").lower()
    if debug_mode == 'y':
        with open(env_file, 'r') as f:
            content = f.read()
        content = content.replace("DEBUG=false", "DEBUG=true")
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ Debug mode enabled")
    
    print("\n🎉 Environment setup completed!")
    print("\nNext steps:")
    print("1. Review your .env file: cat .env")
    print("2. Start the API: python -m app.main")
    print("3. Test the Notion integration: python test_notion_integration.py")

def validate_environment():
    """Validate the current environment configuration"""
    
    print("🔍 Validating Environment Configuration")
    print("=" * 50)
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Run: python setup_env.py")
        return False
    
    # Load and check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    issues = []
    
    # Check Notion configuration
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_DATABASE_ID")
    
    if not notion_token or notion_token == "your_notion_integration_token_here":
        issues.append("NOTION_TOKEN not configured")
    
    if not notion_db_id or notion_db_id == "your_notion_database_id_here":
        issues.append("NOTION_DATABASE_ID not configured")
    
    # Check other configurations
    api_port = os.getenv("API_PORT", "8000")
    debug = os.getenv("DEBUG", "false")
    
    print(f"API Port: {api_port}")
    print(f"Debug Mode: {debug}")
    print(f"Notion Token: {'✅ Configured' if notion_token and notion_token != 'your_notion_integration_token_here' else '❌ Not configured'}")
    print(f"Notion Database ID: {'✅ Configured' if notion_db_id and notion_db_id != 'your_notion_database_id_here' else '❌ Not configured'}")
    
    if issues:
        print(f"\n❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("\n✅ Environment configuration is valid!")
        return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate_environment()
    else:
        setup_environment() 