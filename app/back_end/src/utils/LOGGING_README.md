# KATH Logging System

Comprehensive logging system for the KATH backend with structured logging, request tracing, and performance monitoring.

## Features

- [V] **Structured JSON Logging** for production
- [V] **Colored Console Output** for development
- [V] **Request ID Tracking** for distributed tracing
- [V] **Automatic Request/Response Logging**
- [V] **Performance Metrics** (timing decorators)
- [V] **Log Rotation** (50MB files, 10 backups)
- [V] **Separate Error Logs**
- [V] **Context Managers** for extra metadata

## Quick Start

### Basic Logging

```python
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
logger.critical("Critical message")
```

### Log with Extra Data

```python
logger.info(
    "Processing variant",
    extra={
        'extra_data': {
            'chromosome': 'chr1',
            'position': 12345,
            'gene': 'BRCA1'
        }
    }
)
```

### Performance Logging

```python
from src.utils.logging_config import log_performance

@log_performance("SpliceAI analysis")
def run_spliceai(variants):
    # Your code here
    pass

# Logs: "Performance: SpliceAI analysis completed in 1234.56ms"
```

### Function Call Logging

```python
from src.utils.logging_config import log_function_call

@log_function_call(level=logging.DEBUG)
def calculate_revel_score(chromosome, position):
    # Your code here
    return score

# Logs function entry, exit, duration, and errors
```

### Route Logging

```python
from src.middleware import log_route

@app.route('/api/v1/workspace')
@log_route
def get_workspace():
    # Automatically logs request/response with timing
    return jsonify(data)
```

### Socket.IO Event Logging

```python
from src.middleware import log_socketio_event

@socketio.on('connect')
@log_socketio_event('connect')
def handle_connect():
    # Automatically logs Socket.IO events
    pass
```

## Log Output Formats

### Development (Console)

```
2025-10-27 12:34:56 - kath.routes - INFO - [abc12345] API Request: GET /workspace
2025-10-27 12:34:56 - kath.routes - INFO - [abc12345] API Response: GET /workspace - 200
```

### Production (JSON)

```json
{
  "timestamp": "2025-10-27T12:34:56.789Z",
  "level": "INFO",
  "logger": "kath.routes",
  "message": "API Request: GET /workspace",
  "module": "workspace_route",
  "function": "get_workspace",
  "line": 42,
  "request_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "uuid": "user-uuid-here",
  "sid": "socket-session-id",
  "extra": {
    "method": "GET",
    "path": "/api/v1/workspace"
  }
}
```

## Log Files

All logs are stored in `app/back_end/src/logs/`:

- `kath.log` - All logs (INFO and above)
- `kath_errors.log` - Error logs only (ERROR and above)

**Rotation:** Files rotate at 50MB, keeping 10 backups.

## Configuration

### Environment Variables

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# Set Flask environment (affects log format)
export FLASK_ENV=development  # Colored logs
export FLASK_ENV=production   # JSON logs
```

### Application Setup

The logging system is automatically initialized in `src/__init__.py`:

```python
from src.utils.logging_config import setup_logging

logger = setup_logging(app_name='kath', log_level='INFO')
```

## Request Tracing

Every request gets a unique ID for distributed tracing:

1. **Request ID Generated** - UUID v4 format
2. **Added to Flask `g` object** - `g.request_id`
3. **Included in All Logs** - `request_id` field
4. **Returned in Headers** - `X-Request-ID` response header

### Example Trace

```bash
# Request
GET /api/v1/workspace
Headers: { uuid: "user-123", sid: "session-456" }

# Generated Request ID: abc12345-def6-7890-ghij-klmnopqrstuv

# All logs for this request include:
{
  "request_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "uuid": "user-123",
  "sid": "session-456",
  ...
}

# Response
HTTP/1.1 200 OK
X-Request-ID: abc12345-def6-7890-ghij-klmnopqrstuv
X-Response-Time: 145.23ms
```

## Performance Monitoring

### Automatic Timing

All API requests are automatically timed:

```python
# Logged automatically by middleware
# "API Response: GET /workspace - 200 in 145.23ms"
```

### Custom Timing

```python
from src.utils.logging_config import log_tool_execution
import time

start = time.time()
# ... run tool ...
duration_ms = (time.time() - start) * 1000

log_tool_execution(
    logger,
    tool_name='SpliceAI',
    variants_count=1000,
    duration_ms=duration_ms,
    success=True
)
```

### Database Query Timing

```python
from src.utils.logging_config import log_database_query

start = time.time()
# ... execute query ...
duration_ms = (time.time() - start) * 1000

log_database_query(
    logger,
    query_type='SELECT',
    duration_ms=duration_ms,
    rows_affected=100
)
```

## Context Managers

### Log Context

Add extra data to all logs within a context:

```python
from src.utils.logging_config import LogContext

with LogContext(uuid='user-123', operation='merge'):
    logger.info("Starting merge")  # Includes uuid and operation
    # ... do work ...
    logger.info("Merge complete")  # Includes uuid and operation
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
logger.debug("Detailed debugging info")      # Development only
logger.info("Normal operation")              # General info
logger.warning("Something unexpected")       # Recoverable issues
logger.error("Operation failed", exc_info=True)  # Errors with stack trace
logger.critical("System-wide failure")       # Critical issues
```

### 2. Include Context

```python
# Bad
logger.error("Query failed")

# Good
logger.error(
    "Database query failed",
    exc_info=True,
    extra={
        'extra_data': {
            'query_type': 'SELECT',
            'table': 'variants',
            'file_id': file_id
        }
    }
)
```

### 3. Use Structured Data

```python
# Bad
logger.info(f"Processing {gene} with {len(variants)} variants")

# Good
logger.info(
    "Processing variants for gene",
    extra={
        'extra_data': {
            'gene': gene,
            'variant_count': len(variants)
        }
    }
)
```

### 4. Log Exceptions Properly

```python
try:
    result = process_data(data)
except Exception as e:
    logger.error(
        f"Failed to process data: {str(e)}",
        exc_info=True,  # Include full stack trace
        extra={
            'extra_data': {
                'data_size': len(data),
                'operation': 'process_data'
            }
        }
    )
    raise
```

### 5. Use Decorators for Consistency

```python
# Automatically logs function calls, timing, and errors
@log_function_call()
def complex_operation(arg1, arg2):
    # Your code here
    pass
```

## Querying Logs

### JSON Logs (Production)

Use `jq` for JSON log parsing:

```bash
# Get all ERROR logs
cat kath.log | grep '"level":"ERROR"' | jq .

# Get logs for specific request
cat kath.log | jq 'select(.request_id == "abc12345")'

# Get slow requests (>1000ms)
cat kath.log | jq 'select(.duration_ms > 1000)'

# Get all SpliceAI operations
cat kath.log | jq 'select(.extra.tool_name == "SpliceAI")'

# Get average response time
cat kath.log | jq -s 'map(select(.duration_ms)) | map(.duration_ms) | add/length'
```

### Text Logs (Development)

```bash
# Get all errors
grep ERROR kath.log

# Get logs for specific request ID
grep "abc12345" kath.log

# Get logs for specific user
grep "user-uuid" kath.log

# Tail logs in real-time
tail -f kath.log
```

## Troubleshooting

### No Logs Appearing

1. Check log level: `export LOG_LEVEL=DEBUG`
2. Check log directory permissions: `chmod 755 src/logs`
3. Verify logger is initialized: Check `create_app()` in `src/__init__.py`

### Log Files Too Large

Logs rotate automatically at 50MB. To adjust:

```python
# In logging_config.py
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB instead of 50MB
    backupCount=5  # Keep 5 backups instead of 10
)
```

### Missing Request IDs

Ensure middleware is set up:

```python
from src.middleware import setup_request_logging

setup_request_logging(app)
```

## Migration from Old Logger

### Old Code

```python
from src.utils.logger import Logger

logger = Logger.get(__name__)
logger.info("Message")
```

### New Code

```python
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

The old `logger.py` is deprecated but still works for backward compatibility.

## Advanced Usage

### Custom Formatters

```python
from src.utils.logging_config import setup_logging
import logging

# Create custom logger with specific format
logger = logging.getLogger('custom')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)
```

### Filtering Logs

```python
class UserFilter(logging.Filter):
    def __init__(self, uuid):
        self.uuid = uuid

    def filter(self, record):
        return getattr(record, 'uuid', None) == self.uuid

# Add to handler
handler.addFilter(UserFilter('user-123'))
```

## Integration with Monitoring Tools

### Sentry (Error Tracking)

```python
import sentry_sdk

sentry_sdk.init(dsn="your-sentry-dsn")

# Errors automatically sent to Sentry
logger.error("Error occurred", exc_info=True)
```

### Elasticsearch (Log Aggregation)

Configure Filebeat to ship JSON logs to Elasticsearch:

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    paths:
      - /path/to/kath/logs/*.log
    json.keys_under_root: true

output.elasticsearch:
  hosts: ["localhost:9200"]
```

## Testing

### Testing Logging

```python
import logging
from src.utils.logging_config import get_logger

def test_logging():
    logger = get_logger('test')

    with caplog.at_level(logging.INFO):
        logger.info("Test message")
        assert "Test message" in caplog.text
```

## Summary

The KATH logging system provides:

- [V] Production-ready JSON logging
- [V] Development-friendly colored output
- [V] Request tracing with unique IDs
- [V] Performance monitoring
- [V] Automatic log rotation
- [V] Easy integration with monitoring tools

For questions or issues, see [Developer Setup Guide](../../../docs/DEVELOPER_SETUP.md).
