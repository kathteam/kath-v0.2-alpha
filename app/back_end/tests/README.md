# KATH Backend Tests

Comprehensive test suite for the KATH backend application.

## Directory Structure

```
tests/
 conftest.py              # Pytest configuration and shared fixtures
 pytest.ini              # Pytest settings (in parent directory)
 unit/                   # Unit tests (fast, isolated)
    test_logging.py     # Logging system tests
    test_data_helpers.py # Data processing tests
    test_tools.py       # DNA analysis tool tests
 integration/            # Integration tests (slower, require dependencies)
    test_api_routes.py  # API endpoint tests
 fixtures/               # Shared test data and fixtures
```

## Running Tests

### Install Development Dependencies

```bash
cd app/back_end
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Tests for specific module
pytest tests/unit/test_logging.py

# Tests for DNA tools
pytest -m tools

# Tests for data processing
pytest -m data
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Tests in Parallel

```bash
# Automatically detect number of CPUs
pytest -n auto

# Specify number of workers
pytest -n 4
```

### Run Specific Tests

```bash
# Run a single test function
pytest tests/unit/test_logging.py::TestLoggingSetup::test_setup_logging_creates_logger

# Run a test class
pytest tests/unit/test_logging.py::TestLoggingSetup

# Run tests matching pattern
pytest -k "test_logging"
```

## Test Markers

Tests are categorized using markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests requiring dependencies
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.tools` - DNA analysis tool tests
- `@pytest.mark.data` - Data processing tests
- `@pytest.mark.routes` - API route tests
- `@pytest.mark.utils` - Utility function tests

### Run Tests by Marker

```bash
pytest -m unit
pytest -m "unit and tools"
pytest -m "not slow"
```

## Writing Tests

### Unit Test Example

```python
import pytest
from src.utils.logging_config import get_logger

@pytest.mark.unit
class TestLogging:
    """Tests for logging utilities."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger('test_module')

        assert logger is not None
        assert logger.name == 'test_module'
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
@pytest.mark.routes
class TestWorkspaceRoutes:
    """Integration tests for workspace API routes."""

    def test_get_workspace_structure(self, client, mock_request_headers):
        """Test GET /api/v1/workspace endpoint."""
        response = client.get(
            '/api/v1/workspace',
            headers=mock_request_headers
        )

        assert response.status_code == 200
        assert response.content_type == 'application/json'
```

### Using Fixtures

```python
import pytest

@pytest.mark.unit
def test_with_temp_workspace(temp_workspace):
    """Test using temporary workspace fixture."""
    # temp_workspace is a Path object to a temporary directory
    test_file = temp_workspace / "test.csv"
    test_file.write_text("data")

    assert test_file.exists()

def test_with_mock_variant(mock_variant):
    """Test using mock variant data."""
    assert mock_variant['chromosome'] == 'chr1'
    assert mock_variant['position'] == 12345
```

## Available Fixtures

See `conftest.py` for all available fixtures:

### Application Fixtures

- `app` - Flask application instance
- `client` - Flask test client
- `runner` - Flask CLI runner

### Data Fixtures

- `temp_workspace` - Temporary workspace directory
- `sample_csv_file` - Sample CSV file with variant data
- `large_csv_file` - Large CSV file for pagination testing
- `mock_variant` - Single mock variant dict
- `mock_variants` - List of mock variants
- `mock_pandas_dataframe` - Mock pandas DataFrame

### Mock Fixtures

- `mock_request_headers` - Mock HTTP request headers
- `mock_socketio` - Mock Socket.IO instance
- `mock_redis` - Mock Redis client

### Utility Functions

- `assert_valid_json_response(response, status_code=200)`
- `assert_error_response(response, status_code, error_message_contains=None)`
- `create_mock_file_tree()`

## Test Coverage Goals

- **Overall Coverage:** > 70%
- **Critical Paths:** 100%
- **New Code:** > 80%

### Check Coverage

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html

# Check coverage percentage
pytest --cov=src --cov-fail-under=70
```

## Continuous Integration

Tests run automatically on:

- Pull requests
- Commits to main branch
- Scheduled nightly builds

### CI Configuration

See `.github/workflows/test.yml` for CI configuration.

## Skipping Tests

### Skip Unconditionally

```python
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass
```

### Skip Conditionally

```python
import sys

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_feature():
    pass
```

### Skip if Dependency Missing

```python
from tests.conftest import requires_redis

@requires_redis
def test_redis_connection():
    # Only runs if Redis is available
    pass
```

## Mocking External Dependencies

### Mock HTTP Requests

```python
from unittest.mock import patch

@patch('requests.get')
def test_external_api(mock_get):
    mock_get.return_value.json.return_value = {'data': 'test'}

    # Test code that makes HTTP request
    result = fetch_external_data()

    assert result['data'] == 'test'
    mock_get.assert_called_once()
```

### Mock File System

```python
from unittest.mock import mock_open, patch

@patch('builtins.open', mock_open(read_data='test data'))
def test_file_read():
    with open('test.txt') as f:
        data = f.read()

    assert data == 'test data'
```

### Mock Time

```python
from freezegun import freeze_time
from datetime import datetime

@freeze_time("2025-01-01 12:00:00")
def test_time_dependent_function():
    now = datetime.now()
    assert now.year == 2025
    assert now.hour == 12
```

## Debugging Tests

### Run with Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Local Variables

```bash
pytest -l
```

## Performance Testing

### Benchmark Tests

```python
def test_performance(benchmark):
    """Benchmark a function."""
    result = benchmark(slow_function, arg1, arg2)
    assert result is not None
```

Install pytest-benchmark:

```bash
pip install pytest-benchmark
```

## Common Issues

### Import Errors

If you see import errors, ensure:

1. You're in the `app/back_end` directory
2. Virtual environment is activated
3. All dependencies installed: `pip install -r requirements.txt requirements_dev.txt`

### Redis Connection Errors

If Redis tests fail:

1. Start Redis: `redis-server`
2. Or skip Redis-dependent tests: `pytest -m "not integration"`

### File Permission Errors

Ensure test workspace has write permissions:

```bash
chmod -R 755 tests/
```

## Best Practices

1. **Test Isolation:** Each test should be independent
2. **Clear Names:** Use descriptive test function names
3. **One Assert Per Test:** Focus on single behavior (when possible)
4. **Use Fixtures:** Reuse setup code with fixtures
5. **Mock External Calls:** Don't rely on external services
6. **Test Edge Cases:** Include boundary conditions
7. **Document Complex Tests:** Add docstrings explaining what's tested

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Flask](https://pytest-flask.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Need Help?

- Check existing tests for examples
- See [Developer Setup Guide](../../../docs/DEVELOPER_SETUP.md)
- Ask in team chat or create an issue

---

**Last Updated:** 2025-10-27
