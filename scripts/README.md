# Scripts

This directory contains utility scripts for setting up and managing HouseHunter.

## Available Scripts

### Setup Scripts
- `setup_env.py` - Interactive environment configuration setup
- `setup_notion_database.py` - Notion database setup and configuration

## Usage

### Environment Setup
```bash
python scripts/setup_env.py
```
This script will help you configure your `.env` file with all necessary API keys and settings.

### Notion Database Setup
```bash
python scripts/setup_notion_database.py
```
This script helps set up your Notion database with the correct schema for HouseHunter.

## Prerequisites

- Python 3.8+
- Required dependencies installed (`pip install -r requirements.txt`)
- Access to the services you're configuring (Notion, Telegram, HERE API)

## Notes

- These scripts are for initial setup and configuration
- They should not be run during normal operation
- Always review the generated configuration before using it
