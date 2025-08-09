# Development Documentation

This directory contains development guides, implementation details, and testing information for HouseHunter.

## Implementation Guides

- [Enhanced Route Details](enhanced-route-details.md) - Implementation details for route information features
- [Prediction Times Implementation](prediction-times-implementation.md) - How prediction times are calculated

## Testing

### Test Scripts
The following test scripts are available for development and debugging:

- `test_here_connection.py` - Test HERE API connectivity
- `test_interest_points.py` - Test interest points functionality
- `test_route_details.py` - Test route details calculation
- `test_prediction_times.py` - Test prediction time calculations

### Running Tests
```bash
# Test HERE API connection
python test_here_connection.py

# Test interest points
python test_interest_points.py

# Test route details
python test_route_details.py

# Test prediction times
python test_prediction_times.py
```

### Unit Tests
The main test suite is located in the `tests/` directory and uses pytest:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_telegram_service.py

# Run with coverage
pytest --cov=app
```

## Development Workflow

1. **Feature Development**: Create feature branches from main
2. **Testing**: Write tests for new functionality
3. **Documentation**: Update relevant documentation
4. **Code Review**: Submit pull requests for review
5. **Integration**: Merge to main after approval

## Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Write docstrings for all functions and classes
- Keep functions focused and single-purpose
