"""
This module sets up and configures a Flask application with various extensions and routing.

The module is responsible for:
- Applying gevent monkey patches to enable cooperative multitasking with the standard library.
- Loading environment variables to configure app settings.
- Configuring application settings such as compression and CORS policies.
- Initializing Flask extensions including compression, Socket.IO, and CORS.
- Registering application routes and event handlers.

Dependencies:
- Flask: The core web framework.
- gevent.monkey: Provides monkey patches to enable cooperative multitasking.
- src.setup.extensions: Contains initialization for Flask extensions like compression, Socket.IO,
    and CORS.
- src.setup.router: Defines and manages application routing through blueprints.
- src.setup.eventer: Sets up event handlers for application events.
- src.constants: Provides constants used in configuration, such as BASE_ROUTE.

Returns:
    Flask: A fully configured Flask application instance with all extensions and routes initialized.
"""

# pylint: disable=import-error

import os

import gevent.monkey
from flask import Flask

from .constants import BASE_ROUTE
from .middleware import setup_request_logging
from .routes.workspace_phase2_route import workspace_phase2_route_bp
from .setup.eventer import eventer
from .setup.extensions import compress, cors, env, socketio
from .setup.router import router
from .utils.logging_config import setup_logging


def create_app():
    """
    Create and configure the Flask application.

    This function initializes a Flask application with necessary configurations and extensions.
    It applies gevent monkey patches for cooperative multitasking, sets up application settings
    for compression and CORS, and integrates various Flask extensions such as compression,
    Socket.IO, and CORS. Additionally, it registers the main application routes and sets up
    event handlers.

    Configuration Details:
    - Compression: Enabled for `text/csv` MIME types using gzip with a compression level of 6.
    - Socket.IO: Configured with gevent as the async mode, CORS allowed origins from environment,
        and a Redis message queue.
    - CORS: Applied with origins specified from the environment.

    Returns:
        Flask: A fully configured Flask application instance with extensions initialized,
        routes registered, and event handlers set up.
    """
    # Apply monkey patches for gevent
    gevent.monkey.patch_all()

    # Create Flask app instance
    app = Flask(__name__)

    # Set up centralized logging (must be done early)
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger = setup_logging(app_name="kath", log_level=log_level)
    logger.info("Starting KATH application initialization")

    # Configure app settings
    app.config["COMPRESS_REGISTER"] = False  # disable default compression
    app.config["COMPRESS_MIMETYPES"] = ["text/csv"]
    app.config["COMPRESS_ALGORITHM"] = ["gzip"]
    app.config["COMPRESS_LEVEL"] = 6

    # Set up request logging middleware
    setup_request_logging(app)

    # Initialize Flask extensions with the app instance
    compress.init_app(app)
    logger.info("Compression initialized")
    socketio.init_app(
        app,
        async_mode="gevent",
        cors_allowed_origins=env.get_origins(),
        message_queue=env.get_redis_url(),
        max_http_buffer_size=50 * 1024 * 1024,
    )
    logger.info("Socket.IO initialized")

    cors.init_app(app, resources={r"*": {"origins": env.get_origins()}})
    logger.info("CORS initialized")

    # Initialize database
    from .database import init_db

    init_db(app, create_tables=False)  # Tables already exist from migration
    logger.info("Database initialized")

    # Set up event handlers
    eventer()
    logger.info("Event handlers registered")

    # Register main application routes
    app.register_blueprint(router(BASE_ROUTE))
    logger.info(f"Routes registered at {BASE_ROUTE}")

    # Register Phase 2 routes at top level (not under /api/v1)
    app.register_blueprint(workspace_phase2_route_bp, url_prefix="/workspace_phase2")
    logger.info("Phase 2 routes registered at /workspace_phase2")

    logger.info("KATH application initialization complete")

    return app
