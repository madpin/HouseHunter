# Testing

This directory contains the test suite for HouseHunter.

## Test Structure

### Unit Tests (`tests/`)
- `test_telegram_service.py` - Telegram service unit tests
- `test_notion_integration.py` - Notion integration tests
- `conftest.py` - Pytest configuration and fixtures

### Integration Tests (`tests/integration/`)
- `test_here_connection.py` - HERE API connectivity tests
- `test_interest_points.py` - Interest points functionality tests
- `test_route_details.py` - Route details calculation tests
- `test_prediction_times.py` - Prediction time calculation tests

## Running Tests

### Unit Tests (Pytest)
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all unit tests
pytest

# Run specific test file
pytest tests/test_telegram_service.py

# Run with coverage
pytest --cov=app

# Run with verbose output
pytest -v
```

### Integration Tests
```bash
# Test HERE API connection
python tests/integration/test_here_connection.py

# Test interest points
python tests/integration/test_interest_points.py

# Test route details
python tests/integration/test_route_details.py

# Test prediction times
python tests/integration/test_prediction_times.py
```

## Test Configuration

- **Pytest**: Configured in `conftest.py`
- **Coverage**: Configured for the `app` package
- **Async**: Tests support async/await patterns
- **Mocking**: Uses unittest.mock for isolated testing

## Writing Tests

### Unit Tests
- Test individual functions and methods
- Use mocks for external dependencies
- Follow AAA pattern (Arrange, Act, Assert)
- Keep tests focused and single-purpose

### Integration Tests
- Test complete workflows
- Use real external services when possible
- Clean up test data after tests
- Handle async operations properly

## Best Practices

1. **Test Naming**: Use descriptive test names
2. **Test Isolation**: Each test should be independent
3. **Mock External Services**: Don't rely on external APIs in unit tests
4. **Coverage**: Aim for high test coverage
5. **Documentation**: Document complex test scenarios
