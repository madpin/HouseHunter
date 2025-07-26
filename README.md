# HouseHunter API

A comprehensive FastAPI-based property management system that supports multiple listing websites and provides extensive property data models.

## Features

- **Multi-Website Support**: Ingest properties from multiple real estate websites (Daft.ie, MyHome.ie, etc.)
- **Comprehensive Property Model**: Extensive data model covering all aspects of real estate properties
- **RESTful API**: Full CRUD operations for properties with advanced search capabilities
- **Scalable Architecture**: Clean separation of concerns with services, models, and scrapers
- **Extensible Scraper System**: Easy to add new website scrapers
- **🤖 Telegram Bot Integration**: Send property URLs directly via Telegram for automatic scraping and Notion saving

## 🤖 Telegram Bot Integration

HouseHunter includes a Telegram bot that allows you to send property URLs directly via Telegram and have them automatically scraped and saved to your Notion database.

### Quick Setup
1. Create a bot with @BotFather on Telegram
2. Add `TELEGRAM_BOT_TOKEN=your_token` to your `.env` file
3. Set `TELEGRAM_BOT_ENABLED=true`
4. Start the API - the bot will auto-start
5. Send property URLs to your bot!

📖 **See `telegram_bot_setup.md` for detailed setup instructions.**

## Project Structure

```
HouseHunter/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── property_routes.py  # Property API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── property.py         # Property data models
│   ├── services/
│   │   ├── __init__.py
│   │   └── property_service.py # Business logic layer
│   └── scrapers/
│       ├── __init__.py
│       ├── base_scraper.py     # Base scraper interface
│       ├── daft_scraper.py     # Daft.ie scraper implementation
│       └── scraper_factory.py  # Scraper management
├── requirements.txt
└── README.md
```

## Installation

### Option 1: Local Development

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit the .env file with your values
   nano .env
   ```

### Option 2: Docker Development Environment

1. Clone the repository
2. Start the development environment:
   ```bash
   docker-compose up -d
   ```
3. The API will be available at http://localhost:8000

**VS Code Integration**: 
- Install the "Dev Containers" extension in VS Code
- Open the project in VS Code
- When prompted, click "Reopen in Container" to develop inside the Docker environment
- All Python extensions and linting will be automatically configured

**Development Tools Included**:
- Python 3.11 with all dependencies
- Code formatting (Black, isort)
- Linting (Flake8, Pylint)
- Type checking (MyPy)
- Testing framework (Pytest)
- Hot reloading for development

## Running the API

### Local Development
```bash
uvicorn app.main:app --reload
```

### Docker Development
```bash
# Start the development environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the environment
docker-compose down
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc docs: http://localhost:8000/redoc

## API Endpoints

### Property Management

- `POST /properties/ingest` - Ingest a property from a supported website URL
- `GET /properties/` - Search properties with filters
- `GET /properties/{property_id}` - Get a specific property
- `PUT /properties/{property_id}` - Update a property

### Website Support

- `GET /properties/websites/supported` - Get list of supported websites
- `GET /properties/websites/{website}/properties` - Get properties by website

### Notion Integration

- `POST /notion/properties/save` - Save an existing property to Notion database
- `POST /notion/properties/ingest-and-save` - Ingest a property from URL and save to Notion
- `POST /notion/properties/batch-save` - Save multiple properties to Notion
- `GET /notion/database/info` - Get information about the Notion database
- `GET /notion/database/check` - Check if Notion database is accessible

## Property Data Model

The system uses a comprehensive property model that includes:

- **Core Property Info**: Address, type, bedrooms, bathrooms, area
- **Multiple Listings**: Support for the same property listed on multiple websites
- **Detailed Features**: Energy ratings, amenities, parking, heating
- **Media**: Images with descriptions and ordering
- **Agent Information**: Contact details and agency information
- **Metadata**: Creation dates, update tracking, listing status

## Adding New Website Scrapers

1. Create a new scraper class that inherits from `BaseScraper`
2. Implement the required methods:
   - `can_handle_url()` - Check if the scraper can handle a URL
   - `extract_listing_id()` - Extract listing ID from URL
   - `scrape_property()` - Scrape property data
3. Add the scraper to `ScraperFactory`

Example:
```python
class MyHomeScraper(BaseScraper):
    def __init__(self):
        super().__init__(WebsiteSource.MYHOME)
    
    def can_handle_url(self, url: HttpUrl) -> bool:
        return "myhome.ie" in str(url)
    
    # ... implement other methods
```

## Development

The project follows clean architecture principles with:
- **Models**: Data structures and validation
- **Services**: Business logic and data operations
- **Scrapers**: Website-specific data extraction
- **API Routes**: HTTP endpoint handlers

### Development Tools

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

**Code Quality**:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **Pylint**: Advanced linting
- **MyPy**: Type checking

**Testing**:
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_notion_integration.py

# Run integration tests
python tests/test_notion_integration.py
```

**Pre-commit Hooks** (optional):
```bash
pre-commit install
```

**Setup Scripts**:
```bash
# Set up environment configuration
python scripts/setup_env.py

# Set up Notion database with required properties
python scripts/setup_notion_database.py
```

## Notion Integration

The HouseHunter API includes a comprehensive Notion integration that allows you to save property data directly to a Notion database. This feature enables you to:

- **Organize Properties**: Keep all your property research in a structured Notion database
- **Collaborate**: Share property data with team members through Notion
- **Track Listings**: Monitor property status and updates
- **Custom Views**: Use Notion's powerful database views and filters

### Setup

See [notion_setup.md](notion_setup.md) for detailed setup instructions.

### Environment Variables

The application uses a `.env` file for configuration. Copy the example file and customize it:

```bash
# Set up environment configuration (interactive)
python scripts/setup_env.py

# Or manually copy and edit the environment file
cp env.example .env
# Edit the .env file with your values
```

Required variables for Notion integration:
```bash
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
```

See `env.example` for all available configuration options.

## Future Enhancements

- Database integration (PostgreSQL, MongoDB)
- Authentication and authorization
- Rate limiting and caching
- Background job processing
- Property comparison features
- Market analysis and trends
- Enhanced Notion integration (templates, custom views)
