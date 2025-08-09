# Configuration Files

This directory contains configuration files for HouseHunter.

## Files

### `interest_points_config.json`
Configuration file for interest points (work, shopping centers, transport hubs, etc.).

#### Structure
```json
{
  "interest_points": [
    {
      "id": "dublin_airport",
      "name": "Dublin Airport",
      "latitude": 53.4213,
      "longitude": -6.2701,
      "default_transportation_mode": "PUBLIC_TRANSPORT",
      "active": true
    }
  ]
}
```

#### Usage
- Add your own interest points (work, shopping, transport)
- Set transportation preferences for each location
- Enable/disable specific points as needed

#### Updating
1. Edit the JSON file directly
2. Restart the application to load changes
3. Use the API endpoints to manage points dynamically

## Environment Variables

Most configuration is handled through environment variables in your `.env` file. See the setup documentation for details.

## Validation

Configuration files are validated on startup. Invalid configurations will cause the application to fail with helpful error messages.
