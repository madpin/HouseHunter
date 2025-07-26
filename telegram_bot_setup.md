# Telegram Bot Setup Guide

This guide will help you set up the Telegram bot integration for HouseHunter to automatically ingest property URLs and save them to your Notion database.

## Prerequisites

1. A Telegram account
2. A configured Notion integration (see `notion_setup.md`)
3. HouseHunter API running with proper configuration

## Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a conversation with BotFather
3. Send the command `/newbot`
4. Follow the prompts:
   - Choose a name for your bot (e.g., "HouseHunter Property Bot")
   - Choose a username for your bot (must end with 'bot', e.g., "myhousehunter_bot")
5. BotFather will provide you with a bot token that looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
6. **Important**: Keep this token secure and never share it publicly

## Step 2: Configure Environment Variables

Add the following variables to your `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_ENABLED=true
```

Example:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_ENABLED=true
```

## Step 3: Install Dependencies

If you haven't already installed the updated dependencies, run:

```bash
pip install -r requirements.txt
```

## Step 4: Start the API Server

Start your HouseHunter API server:

```bash
python -m app.main
```

Or using uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

If `TELEGRAM_BOT_ENABLED=true`, the bot will start automatically when the API starts.

## Step 5: Test Your Bot

1. Open Telegram and search for your bot by username
2. Start a conversation with your bot
3. Send `/start` to see the welcome message
4. Send `/help` to see available commands

## Bot Commands

### Available Commands

- **`/start`** - Show welcome message and basic information
- **`/help`** - Get detailed help information
- **`/status`** - Check bot and database connection status
- **`/supported`** - List all supported property websites

### Using the Bot

To add a property to your Notion database:

1. Find a property listing on a supported website (e.g., Daft.ie)
2. Copy the property URL
3. Send the URL to your bot
4. The bot will:
   - Validate the URL
   - Scrape the property details
   - Save the property to your Notion database
   - Send you a confirmation with property details

### Example Usage

```
User: https://www.daft.ie/for-sale/house-123-main-street-dublin-1-dublin-1/1234567

Bot: 🔄 Processing property URL...
     📍 https://www.daft.ie/for-sale/house-123-main-street-dublin-1-dublin-1/1234567

Bot: ✅ Property saved successfully!

     🏠 House
     📍 Dublin 1, Dublin
     🛏️ 3 bed, 2 bath
     📐 120m²
     💰 €450,000

     📋 View in Notion
     🔗 Original listing
```

## API Management

You can also manage the bot via API endpoints:

### Check Bot Status
```bash
GET /telegram/status
```

### Start Bot
```bash
POST /telegram/start
```

### Stop Bot
```bash
POST /telegram/stop
```

### Restart Bot
```bash
POST /telegram/restart
```

### Get Configuration
```bash
GET /telegram/config
```

## Supported Websites

The bot currently supports the same websites as the main scraping system:
- Daft.ie
- (Additional scrapers can be added to the system)

To check supported websites via the bot, send `/supported` command.

## Troubleshooting

### Bot Not Responding

1. **Check Bot Token**: Ensure `TELEGRAM_BOT_TOKEN` is correctly set
2. **Check API Status**: Verify the API server is running
3. **Check Bot Status**: Use `/telegram/status` API endpoint
4. **Check Logs**: Look at server logs for error messages

### Bot Can't Save to Notion

1. **Verify Notion Setup**: Ensure Notion integration is properly configured
2. **Check Database Permissions**: Make sure the bot has access to your Notion database
3. **Use `/status` Command**: Check database connection status via the bot

### URL Not Supported

1. **Check Supported Sites**: Use `/supported` command to see available websites
2. **Verify URL Format**: Ensure the URL is complete and valid
3. **Add New Scrapers**: Contact developers to add support for additional websites

## Security Considerations

1. **Keep Bot Token Secret**: Never share your bot token publicly
2. **Restrict Bot Access**: Only share your bot with trusted users
3. **Monitor Usage**: Check logs regularly for unusual activity
4. **Environment Variables**: Store sensitive data in environment variables, not in code

## Advanced Features

### Multiple Users
- The bot can handle multiple users simultaneously
- Each user's requests are processed independently
- All properties are saved to the same Notion database

### Error Handling
- The bot provides detailed error messages for failed operations
- All errors are logged for debugging purposes
- Users receive helpful feedback for common issues

### Logging
- All bot interactions are logged with user information
- Property processing steps are tracked
- Error details are captured for troubleshooting

## Development Notes

### Adding New Commands
To add new commands, modify `app/services/telegram_service.py`:
1. Create a new command handler function
2. Add the handler in `setup_handlers()` method

### Customizing Messages
Bot messages can be customized by modifying the message strings in the TelegramService class.

### Integration with Other Services
The bot is designed to integrate seamlessly with existing HouseHunter services:
- Uses the same ScraperFactory for website support
- Leverages existing NotionService for database operations
- Integrates with PropertyService for data management

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review server logs for detailed error information
3. Verify all configuration settings
4. Test individual components (API, Notion, scrapers) separately 