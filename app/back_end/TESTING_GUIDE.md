# KATH Backend Testing Guide

Quick reference for running tests using the test runner scripts.

## Quick Start

### Mac/Linux

```bash
# Make script executable (first time only)
chmod +x run_tests.sh

# Run all tests
./run_tests.sh

# Run specific test categories
./run_tests.sh unit
./run_tests.sh coverage
```

### Windows

```cmd
# Run all tests
run_tests.bat

# Run specific test categories
run_tests.bat unit
run_tests.bat coverage
```

---

## Available Commands

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `all` | Run all tests (default) | `./run_tests.sh` |
| `unit` | Run unit tests only | `./run_tests.sh unit` |
| `integration` | Run integration tests | `./run_tests.sh integration` |
| `fast` | Run fast tests (exclude slow) | `./run_tests.sh fast` |

### Category-Specific Tests

| Command | Description | What it tests |
|---------|-------------|---------------|
| `tools` | DNA analysis tools | SpliceAI, CADD, REVEL |
| `data` | Data processing | CSV handling, filtering, aggregation |
| `routes` | API endpoints | All Flask routes |

### Coverage Reports

| Command | Description | Output |
|---------|-------------|--------|
| `coverage` | Run with coverage | Terminal report + HTML |
| `coverage-html` | Generate HTML report | Opens in browser |

### Performance Options

| Command | Description | Notes |
|---------|-------------|-------|
| `parallel` | Run tests in parallel | Requires pytest-xdist |
| `verbose` | Verbose output | Shows detailed test info |
| `watch` | Watch mode | Re-runs on file changes |

### Debugging

| Command | Description | Use case |
|---------|-------------|----------|
| `failed` | Re-run failed tests | After fixing bugs |
| `specific FILE` | Run specific file | Target one test file |

### Utilities

| Command | Description |
|---------|-------------|
| `clean` | Remove test artifacts |
| `check` | Verify test environment |
| `help` | Show usage information |

---

## Common Usage Examples

### Development Workflow

```bash
# 1. Run fast tests during development
./run_tests.sh fast

# 2. Run specific test file you're working on
./run_tests.sh specific tests/unit/test_logging.py

# 3. Run with coverage before committing
./run_tests.sh coverage

# 4. Check if environment is set up correctly
./run_tests.sh check
```

### Pre-Commit Checklist

```bash
# 1. Run all unit tests
./run_tests.sh unit

# 2. Check coverage (should be > 70%)
./run_tests.sh coverage

# 3. Run integration tests if Redis available
./run_tests.sh integration

# 4. Clean up artifacts
./run_tests.sh clean
```

### CI/CD Simulation

```bash
# Run tests exactly as CI will run them
./run_tests.sh parallel
./run_tests.sh coverage
```

### Debugging Failed Tests

```bash
# 1. Run failed tests only
./run_tests.sh failed

# 2. Run with verbose output
./run_tests.sh verbose

# 3. Run specific failing test
./run_tests.sh specific tests/unit/test_tools.py
```

---

## Additional pytest Options

You can pass additional pytest options after the command:

```bash
# Stop on first failure
./run_tests.sh unit -x

# Show print statements
./run_tests.sh unit -s

# Run tests matching pattern
./run_tests.sh all -k "test_logging"

# Drop into debugger on failure
./run_tests.sh unit --pdb

# Show local variables in tracebacks
./run_tests.sh all -l

# Extra verbose
./run_tests.sh all -vv
```

### Combining Options

```bash
# Verbose + stop on first failure + show prints
./run_tests.sh unit -vv -x -s

# Run specific marker with coverage
./run_tests.sh coverage -m tools

# Parallel execution with verbose output
./run_tests.sh parallel -v
```

---

## Test Markers

Use markers to run specific test categories:

```bash
# Run tests with specific marker
pytest -m unit              # Unit tests
pytest -m integration       # Integration tests
pytest -m tools             # Tool tests
pytest -m data              # Data processing tests
pytest -m routes            # API route tests
pytest -m slow              # Slow tests
pytest -m "unit and tools"  # Combined markers
pytest -m "not slow"        # Exclude slow tests
```

---

## Understanding Test Output

### Success Output

```
========== test session starts ==========
collected 45 items

tests/unit/test_logging.py ............ [ 26%]
tests/unit/test_data_helpers.py ....... [ 42%]
tests/unit/test_tools.py .............. [ 73%]
tests/integration/test_api_routes.py ... [100%]

========== 45 passed in 2.34s ==========

[SUCCESS] All tests passed! 
```

### Failure Output

```
========== FAILURES ==========
_____ TestLogging.test_example _____

    def test_example():
>       assert False
E       assert False

tests/unit/test_logging.py:10: AssertionError

========== short test summary info ==========
FAILED tests/unit/test_logging.py::TestLogging::test_example

========== 1 failed, 44 passed in 2.56s ==========

[ERROR] Some tests failed! 
```

### Coverage Report

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/__init__.py                  45      2    96%   23, 67
src/utils/logging_config.py     120      5    96%   145-149
src/tools/revel.py               67      8    88%   34-41
-----------------------------------------------------------
TOTAL                          1234     45    96%

[SUCCESS] Tests completed! Coverage report generated.
[INFO] View HTML report: open htmlcov/index.html
```

---

## Troubleshooting

### "pytest: command not found"

```bash
# Install test dependencies
pip install -r requirements_dev.txt

# Or activate virtual environment first
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### "Virtual environment not activated"

The script will try to activate it automatically. If it fails:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate.bat # Windows

# Install dependencies
pip install -r requirements.txt requirements_dev.txt
```

### "Redis connection failed"

Some integration tests require Redis:

```bash
# Install Redis
# Mac: brew install redis
# Ubuntu: sudo apt install redis-server
# Windows: Use WSL or Redis for Windows

# Start Redis
redis-server

# Or skip integration tests
./run_tests.sh unit
```

### Permission denied

```bash
# Make script executable
chmod +x run_tests.sh
```

### Tests are slow

```bash
# Run in parallel
./run_tests.sh parallel

# Or run only fast tests
./run_tests.sh fast
```

---

## Best Practices

### During Development

1. **Run fast tests frequently**

   ```bash
   ./run_tests.sh fast
   ```

2. **Use watch mode for TDD**

   ```bash
   ./run_tests.sh watch
   ```

3. **Test specific modules you're working on**

   ```bash
   ./run_tests.sh specific tests/unit/test_logging.py
   ```

### Before Committing

1. **Run all unit tests**

   ```bash
   ./run_tests.sh unit
   ```

2. **Check coverage**

   ```bash
   ./run_tests.sh coverage
   ```

3. **Run integration tests**

   ```bash
   ./run_tests.sh integration
   ```

4. **Clean artifacts**

   ```bash
   ./run_tests.sh clean
   ```

### In CI/CD

```bash
# Parallel execution for speed
./run_tests.sh parallel

# With coverage reporting
./run_tests.sh coverage

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=70
```

---

## Advanced Usage

### Custom pytest Configuration

Edit `pytest.ini` to customize:

- Test discovery patterns
- Coverage settings
- Markers
- Warning filters

### Creating New Tests

See `tests/README.md` for detailed guide on writing tests.

Quick template:

```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    """Tests for my feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        result = my_function()
        assert result is not None
```

### Continuous Testing

Use `watch` mode for continuous testing:

```bash
./run_tests.sh watch
```

This will automatically re-run tests when you save files.

---

## Summary

**Most common commands:**

```bash
# Development
./run_tests.sh fast
./run_tests.sh specific tests/unit/test_file.py

# Pre-commit
./run_tests.sh unit
./run_tests.sh coverage

# Debugging
./run_tests.sh failed
./run_tests.sh verbose
```

**For more details:** See `tests/README.md`

---

**Questions?** Check the [Developer Setup Guide](../../docs/DEVELOPER_SETUP.md) or create an issue.
