# Notion Integration Setup Guide

This guide will help you set up the Notion integration for the HouseHunter API.

## Prerequisites

1. A Notion account
2. A Notion integration token
3. A Notion database to store properties

## Step 1: Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give your integration a name (e.g., "HouseHunter Property Manager")
4. Select the workspace where you want to use the integration
5. Click "Submit"
6. Copy the "Internal Integration Token" - you'll need this for the API

## Step 2: Create a Notion Database

1. Create a new page in Notion
2. Add a database to the page
3. Configure the database with the following properties:

### Required Properties:
- **Title** (Title type) - Will contain property name and address
- **Address** (Text type) - Full property address
- **Property Type** (Select type) - House, Apartment, etc.
- **City** (Text type) - City name
- **County** (Text type) - County name
- **Bedrooms** (Number type) - Number of bedrooms
- **Bathrooms** (Number type) - Number of bathrooms
- **Area (sqm)** (Number type) - Property area in square meters
- **Price** (Text type) - Formatted price information
- **Energy Rating** (Text type) - Energy efficiency rating
- **Year Built** (Number type) - Construction year
- **Status** (Select type) - Active/Inactive
- **Date Added** (Date type) - When the property was added

### Optional Properties:
- **Lot Size (sqm)** (Number type) - Lot size in square meters
- **New Build** (Checkbox type) - Whether it's a new build
- **Furnished** (Checkbox type) - Whether it's furnished
- **Parking** (Text type) - Parking information
- **Heating** (Text type) - Heating system information

## Step 3: Get Database ID

1. Open your database in Notion
2. Copy the URL from your browser
3. The database ID is the part after the last `/` and before the `?` in the URL
   - Example: `https://www.notion.so/workspace/1234567890abcdef1234567890abcdef?v=...`
   - Database ID: `1234567890abcdef1234567890abcdef`

## Step 4: Configure Environment Variables

### Option 1: Using .env file (Recommended)

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit the `.env` file and add your Notion credentials:
   ```env
   # Notion Integration
   NOTION_TOKEN=your_integration_token_here
   NOTION_DATABASE_ID=your_database_id_here
   ```

### Option 2: Using environment variables

Set the following environment variables:

```bash
# Notion API configuration
export NOTION_TOKEN="your_integration_token_here"
export NOTION_DATABASE_ID="your_database_id_here"
```

## Step 5: Share Database with Integration

1. Open your database in Notion
2. Click the "Share" button in the top right
3. Click "Invite"
4. Search for your integration name
5. Select it and click "Invite"
6. Make sure it has "Can edit" permissions

## Step 6: Test the Integration

1. Start the HouseHunter API
2. Check if the database is accessible:
   ```bash
   curl http://localhost:8000/notion/database/check
   ```

3. Get database information:
   ```bash
   curl http://localhost:8000/notion/database/info
   ```

## API Endpoints

Once configured, you can use these endpoints:

### Save Existing Property to Notion
```bash
POST /notion/properties/save
{
  "property_id": "your_property_id"
}
```

### Ingest and Save Property from URL
```bash
POST /notion/properties/ingest-and-save
{
  "url": "https://www.daft.ie/property/example"
}
```

### Batch Save Properties
```bash
POST /notion/properties/batch-save
{
  "property_ids": ["id1", "id2", "id3"]
}
```

## Troubleshooting

### Common Issues:

1. **"Notion token is required"**
   - Make sure `NOTION_TOKEN` environment variable is set
   - Verify the token is correct

2. **"Notion database ID is required"**
   - Make sure `NOTION_DATABASE_ID` environment variable is set
   - Verify the database ID is correct

3. **"Database not accessible"**
   - Make sure the integration has been shared with the database
   - Verify the integration has "Can edit" permissions

4. **"Property not found"**
   - Make sure the property exists in the HouseHunter database
   - Verify the property ID is correct

### Testing with Docker

The Docker setup automatically loads environment variables from the `.env` file. Make sure your `.env` file is in the project root directory.

If you prefer to pass environment variables directly:

```bash
docker run -e NOTION_TOKEN=your_token -e NOTION_DATABASE_ID=your_db_id househunter-api
```

The `docker-compose.yml` is already configured to use the `.env` file:

```yaml
services:
  househunter-api:
    env_file:
      - .env
```

## Database Schema Example

Here's an example of how your Notion database should be structured:

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Property name and address |
| Address | Text | Full address |
| Property Type | Select | House, Apartment, etc. |
| City | Text | City name |
| County | Text | County name |
| Bedrooms | Number | Number of bedrooms |
| Bathrooms | Number | Number of bathrooms |
| Area (sqm) | Number | Property area |
| Price | Text | Formatted price |
| Energy Rating | Text | Energy efficiency |
| Year Built | Number | Construction year |
| Status | Select | Active/Inactive |
| Date Added | Date | When added |

The API will automatically populate these fields when saving properties to Notion. 