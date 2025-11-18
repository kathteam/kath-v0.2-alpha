"""
Logging middleware for Flask application.

Provides:
- Request ID generation for distributed tracing
- Automatic request/response logging
- Performance timing
- Error logging
"""

import logging
import time
import uuid
from functools import wraps
from typing import Callable

from flask import Flask, g, request

from src.utils.logging_config import get_logger, log_api_request, log_api_response

logger = get_logger(__name__)


def generate_request_id() -> str:
    """Generate unique request ID."""
    return str(uuid.uuid4())


def setup_request_logging(app: Flask):
    """
    Set up request logging middleware for Flask app.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request():
        """Execute before each request."""
        # Generate request ID
        g.request_id = generate_request_id()

        # Extract user identifiers from headers
        g.uuid = request.headers.get("uuid", "anonymous")
        g.sid = request.headers.get("sid", "no-session")

        # Store request start time
        g.start_time = time.time()

        # Log request
        log_api_request(logger, method=request.method, path=request.path, uuid=g.uuid, sid=g.sid)

        # Log request body for non-GET requests (truncated)
        if request.method != "GET" and request.is_json:
            logger.debug(
                f"Request body: {str(request.get_json())[:500]}",
                extra={"extra_data": {"request_id": g.request_id, "content_type": request.content_type}},
            )

    @app.after_request
    def after_request(response):
        """Execute after each request."""
        # Calculate request duration
        duration_ms = (time.time() - g.get("start_time", time.time())) * 1000

        # Log response
        log_api_response(
            logger, method=request.method, path=request.path, status_code=response.status_code, duration_ms=duration_ms
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = g.get("request_id", "unknown")

        # Add performance timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Log unhandled exceptions."""
        logger.error(
            f"Unhandled exception: {str(error)}",
            exc_info=True,
            extra={
                "extra_data": {
                    "request_id": g.get("request_id", "unknown"),
                    "path": request.path,
                    "method": request.method,
                    "uuid": g.get("uuid", "unknown"),
                    "sid": g.get("sid", "unknown"),
                }
            },
        )

        # Re-raise to let Flask handle the error response
        raise


def log_route(func: Callable) -> Callable:
    """
    Decorator for route handlers to add detailed logging.

    Example:
        @app.route('/api/v1/workspace')
        @log_route
        def get_workspace():
            # ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(
            f"Executing route handler: {func.__name__}",
            extra={"extra_data": {"function": func.__name__, "args": str(args)[:200], "kwargs": str(kwargs)[:200]}},
        )

        try:
            result = func(*args, **kwargs)
            logger.debug(f"Route handler completed: {func.__name__}")
            return result

        except Exception as e:
            logger.error(f"Route handler error in {func.__name__}: {str(e)}", exc_info=True)
            raise

    return wrapper


def log_socketio_event(event_name: str):
    """
    Decorator for Socket.IO event handlers.

    Example:
        @socketio.on('connect')
        @log_socketio_event('connect')
        def handle_connect():
            # ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(
                f"Socket.IO event: {event_name}", extra={"extra_data": {"event": event_name, "function": func.__name__}}
            )

            try:
                result = func(*args, **kwargs)
                logger.debug(f"Socket.IO event completed: {event_name}")
                return result

            except Exception as e:
                logger.error(f"Socket.IO event error in {event_name}: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator


__all__ = [
    "setup_request_logging",
    "log_route",
    "log_socketio_event",
    "generate_request_id",
]
