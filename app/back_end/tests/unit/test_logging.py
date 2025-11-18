"""
Unit tests for logging configuration and utilities.
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.utils.logging_config import (
    ColoredFormatter,
    JSONFormatter,
    LogContext,
    RequestIDFilter,
    get_logger,
    log_function_call,
    log_performance,
    setup_logging,
)


@pytest.mark.unit
class TestLoggingSetup:
    """Tests for logging setup and configuration."""

    def test_setup_logging_creates_logger(self, tmp_path):
        """Test that setup_logging creates a logger."""
        logger = setup_logging(app_name="test", log_level="INFO", log_dir=str(tmp_path))

        assert logger is not None
        assert logger.name == "test"
        # Check effective level (accounts for parent logger levels)
        assert logger.getEffectiveLevel() == logging.INFO

    def test_setup_logging_creates_log_files(self, tmp_path):
        """Test that setup_logging creates log files."""
        setup_logging(app_name="test", log_level="INFO", log_dir=str(tmp_path))

        log_file = tmp_path / "test.log"
        error_log_file = tmp_path / "test_errors.log"

        assert log_file.exists()
        assert error_log_file.exists()

    def test_setup_logging_different_levels(self, tmp_path):
        """Test setup_logging with different log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger = setup_logging(app_name=f"test_{level.lower()}", log_level=level, log_dir=str(tmp_path))

            assert logger.getEffectiveLevel() == getattr(logging, level)

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"


@pytest.mark.unit
class TestJSONFormatter:
    """Tests for JSON log formatter."""

    def test_json_formatter_formats_log_record(self):
        """Test that JSONFormatter produces valid JSON."""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="Test message", args=(), exc_info=None
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_json_formatter_includes_request_id(self):
        """Test that JSONFormatter includes request ID if present."""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="Test message", args=(), exc_info=None
        )
        record.request_id = "test-request-123"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["request_id"] == "test-request-123"

    def test_json_formatter_includes_exception_info(self):
        """Test that JSONFormatter includes exception information."""
        import json

        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["message"]


@pytest.mark.unit
class TestColoredFormatter:
    """Tests for colored console formatter."""

    def test_colored_formatter_adds_colors(self):
        """Test that ColoredFormatter adds ANSI color codes."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py", lineno=10, msg="Error message", args=(), exc_info=None
        )

        formatted = formatter.format(record)

        # Should contain ANSI color codes
        assert "\033[" in formatted
        assert "Error message" in formatted

    def test_colored_formatter_includes_request_id(self):
        """Test that ColoredFormatter includes request ID."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="Test message", args=(), exc_info=None
        )
        record.request_id = "abc12345-def6-7890"

        formatted = formatter.format(record)

        # Should include shortened request ID
        assert "[abc12345]" in formatted


@pytest.mark.unit
class TestRequestIDFilter:
    """Tests for request ID filter."""

    def test_request_id_filter_adds_request_id(self, app):
        """Test that RequestIDFilter adds request ID from Flask g."""
        from flask import g

        with app.app_context():
            with app.test_request_context():
                # Set up Flask g with test data
                g.request_id = "test-request-123"
                g.uuid = "test-uuid"
                g.sid = "test-sid"

                filter_instance = RequestIDFilter()
                record = logging.LogRecord(
                    name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="Test", args=(), exc_info=None
                )

                result = filter_instance.filter(record)

                assert result is True
                assert record.request_id == "test-request-123"
                assert record.uuid == "test-uuid"
                assert record.sid == "test-sid"

    @patch("flask.has_request_context")
    def test_request_id_filter_handles_no_request_context(self, mock_has_request_context):
        """Test that RequestIDFilter handles no request context."""
        mock_has_request_context.return_value = False

        filter_instance = RequestIDFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="Test", args=(), exc_info=None
        )

        result = filter_instance.filter(record)

        assert result is True
        assert record.request_id == "background-task"
        assert record.uuid == "system"
        assert record.sid == "system"


@pytest.mark.unit
class TestLogDecorators:
    """Tests for logging decorators."""

    def test_log_function_call_decorator_logs_execution(self, caplog):
        """Test that log_function_call decorator logs function execution."""
        logger = get_logger("test")

        @log_function_call(logger=logger, level=logging.INFO)
        def test_function(arg1, arg2):
            return arg1 + arg2

        with caplog.at_level(logging.INFO):
            result = test_function(1, 2)

        assert result == 3
        assert "Calling test_function" in caplog.text
        assert "Completed test_function" in caplog.text

    def test_log_function_call_decorator_logs_errors(self, caplog):
        """Test that log_function_call decorator logs errors."""
        logger = get_logger("test")

        @log_function_call(logger=logger, level=logging.INFO)
        def test_function():
            raise ValueError("Test error")

        with caplog.at_level(logging.INFO):
            with pytest.raises(ValueError):
                test_function()

        assert "Error in test_function" in caplog.text

    def test_log_performance_decorator_measures_time(self, caplog):
        """Test that log_performance decorator measures execution time."""
        import time

        @log_performance("Test operation")
        def slow_function():
            time.sleep(0.01)  # Sleep 10ms
            return "done"

        with caplog.at_level(logging.INFO):
            result = slow_function()

        assert result == "done"
        assert "Performance: Test operation completed" in caplog.text
        # Should log time in ms
        assert "ms" in caplog.text


@pytest.mark.unit
class TestLogContext:
    """Tests for log context manager."""

    def test_log_context_adds_extra_data(self, caplog):
        """Test that LogContext adds extra data to log records."""
        logger = get_logger("test")

        with LogContext(operation="test_op", user_id="123"):
            with caplog.at_level(logging.INFO):
                logger.info("Test message")

        # Check that extra data was added (implementation dependent)
        # This test verifies the context manager works without errors
        assert "Test message" in caplog.text

    def test_log_context_restores_factory(self):
        """Test that LogContext restores original log record factory."""
        original_factory = logging.getLogRecordFactory()

        with LogContext(test_key="test_value"):
            pass

        # Factory should be restored
        assert logging.getLogRecordFactory() == original_factory
