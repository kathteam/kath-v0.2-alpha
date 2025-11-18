"""
Centralized logging configuration for KATH backend.

This module provides:
- Structured JSON logging for production
- Human-readable logging for development
- Request ID tracking for distributed tracing
- Automatic log rotation
- Performance timing decorators
"""

import functools
import json
import logging
import logging.handlers
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add user UUID if available
        if hasattr(record, "uuid"):
            log_data["uuid"] = record.uuid

        # Add session ID if available
        if hasattr(record, "sid"):
            log_data["sid"] = record.sid

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] is not None else "Unknown",
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add performance metrics if available
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development console output.

    Uses ANSI color codes to make logs more readable.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        # Add request ID if available
        request_id = getattr(record, "request_id", None)
        if request_id:
            record.msg = f"[{request_id[:8]}] {record.msg}"

        return super().format(record)


class RequestIDFilter(logging.Filter):
    """
    Filter to add request ID to log records.

    Retrieves request ID from Flask request context if available.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to record."""
        from flask import g, has_request_context

        if has_request_context():
            record.request_id = getattr(g, "request_id", "no-request-id")
            record.uuid = getattr(g, "uuid", "no-uuid")
            record.sid = getattr(g, "sid", "no-sid")
        else:
            record.request_id = "background-task"
            record.uuid = "system"
            record.sid = "system"

        return True


def setup_logging(app_name: str = "kath", log_level: str = "INFO", log_dir: Optional[str] = None) -> logging.Logger:
    """
    Set up centralized logging configuration.

    Args:
        app_name: Name of the application (used for logger name and log file)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: src/logs)

    Returns:
        Configured root logger
    """
    # Determine environment
    env = os.getenv("FLASK_ENV", "production")
    is_development = env == "development"

    # Create log directory
    log_dir_path: Path
    if log_dir is None:
        log_dir_path = Path(__file__).parent.parent / "logs"
    else:
        log_dir_path = Path(log_dir)

    log_dir_path.mkdir(mode=0o755, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console Handler (development: colored, production: JSON)
    console_handler = logging.StreamHandler()
    console_formatter: logging.Formatter
    if is_development:
        console_formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        console_formatter = JSONFormatter()

    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(console_handler)

    # File Handler - Always JSON for easy parsing
    log_file = log_dir_path / f"{app_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, mode="a", maxBytes=50 * 1024 * 1024, backupCount=10, encoding="utf-8"  # 50MB
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(file_handler)

    # Error File Handler - Separate file for errors
    error_log_file = log_dir_path / f"{app_name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, mode="a", maxBytes=50 * 1024 * 1024, backupCount=10, encoding="utf-8"  # 50MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    error_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(error_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("engineio").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.WARNING)

    logger = logging.getLogger(app_name)
    logger.info(f"Logging initialized", extra={"extra_data": {"level": log_level, "environment": env}})

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(logger: Optional[logging.Logger] = None, level: int = logging.DEBUG):
    """
    Decorator to log function calls with arguments and execution time.

    Args:
        logger: Logger instance (default: creates logger from function module)
        level: Log level for the message

    Example:
        @log_function_call()
        def my_function(arg1, arg2):
            return arg1 + arg2
    """

    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Log function entry
            logger.log(
                level,
                f"Calling {func.__name__}",
                extra={"extra_data": {"args": str(args)[:200], "kwargs": str(kwargs)[:200]}},  # Truncate long args
            )

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Log successful completion
                logger.log(
                    level,
                    f"Completed {func.__name__}",
                    extra={"extra_data": {"duration_ms": round(duration_ms, 2), "success": True}},
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                # Log error
                logger.error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={"extra_data": {"duration_ms": round(duration_ms, 2), "success": False}},
                )
                raise

        return wrapper

    return decorator


def log_performance(operation: str):
    """
    Decorator to log performance metrics for operations.

    Args:
        operation: Description of the operation being timed

    Example:
        @log_performance("Database query")
        def query_database():
            # ...
    """

    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Log performance
                log_record = logger.makeRecord(
                    logger.name,
                    logging.INFO,
                    func.__code__.co_filename,
                    func.__code__.co_firstlineno,
                    f"Performance: {operation} completed in {duration_ms:.2f}ms",
                    (),
                    None,
                    func.__name__,
                )
                log_record.duration_ms = round(duration_ms, 2)
                log_record.operation = operation
                logger.handle(log_record)

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Performance: {operation} failed after {duration_ms:.2f}ms: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator


class LogContext:
    """
    Context manager for adding extra data to log records.

    Example:
        with LogContext(request_id='abc123', uuid='user-uuid'):
            logger.info("Processing request")
    """

    def __init__(self, **kwargs):
        """Initialize with extra data."""
        self.extra_data = kwargs
        self.old_factory = None

    def __enter__(self):
        """Add extra data to log records."""
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.extra_data.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        self.old_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original log record factory."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Convenience functions for common log patterns


def log_api_request(logger: logging.Logger, method: str, path: str, uuid: str, sid: str):
    """Log API request."""
    logger.info(
        f"API Request: {method} {path}",
        extra={"extra_data": {"method": method, "path": path, "uuid": uuid, "sid": sid}},
    )


def log_api_response(logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float):
    """Log API response."""
    log_record = logger.makeRecord(
        logger.name, logging.INFO, __file__, 0, f"API Response: {method} {path} - {status_code}", (), None
    )
    log_record.duration_ms = round(duration_ms, 2)
    log_record.extra_data = {"method": method, "path": path, "status_code": status_code}
    logger.handle(log_record)


def log_tool_execution(logger: logging.Logger, tool_name: str, variants_count: int, duration_ms: float, success: bool):
    """Log DNA analysis tool execution."""
    level = logging.INFO if success else logging.ERROR
    message = f"Tool {tool_name}: Processed {variants_count} variants in {duration_ms:.2f}ms"

    log_record = logger.makeRecord(logger.name, level, __file__, 0, message, (), None)
    log_record.duration_ms = round(duration_ms, 2)
    log_record.extra_data = {"tool_name": tool_name, "variants_count": variants_count, "success": success}
    logger.handle(log_record)


def log_database_query(logger: logging.Logger, query_type: str, duration_ms: float, rows_affected: int = 0):
    """Log database query performance."""
    log_record = logger.makeRecord(
        logger.name,
        logging.DEBUG,
        __file__,
        0,
        f"Database {query_type}: {rows_affected} rows in {duration_ms:.2f}ms",
        (),
        None,
    )
    log_record.duration_ms = round(duration_ms, 2)
    log_record.extra_data = {"query_type": query_type, "rows_affected": rows_affected}
    logger.handle(log_record)


# Export public API
__all__ = [
    "setup_logging",
    "get_logger",
    "log_function_call",
    "log_performance",
    "LogContext",
    "log_api_request",
    "log_api_response",
    "log_tool_execution",
    "log_database_query",
]
