"""
Database Configuration Module

Handles database initialization, configuration, and SQLAlchemy setup.
"""

import os
from pathlib import Path

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src.settings import get_settings

# Global session object
db_session = None


def get_database_uri():
    """
    Get the database URI from settings.

    Returns:
        str: SQLite database URI
    """
    settings = get_settings()
    db_path = settings.database_path

    if not db_path:
        # Default to database in instance folder
        db_path = os.path.join(os.getcwd(), "instance", "kath.db")

    # Ensure absolute path
    db_path = os.path.abspath(db_path)

    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    Path(db_dir).mkdir(parents=True, exist_ok=True)

    return f"sqlite:///{db_path}"


def configure_database(app: Flask):
    """
    Configure SQLAlchemy with the application.

    Args:
        app (Flask): Flask application instance
    """
    global db_session

    settings = get_settings()
    database_uri = get_database_uri()

    # Store in app config for reference
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

    # Create engine with optimized connection pool settings
    engine_options = {
        "pool_size": 20,  # Increased from 10 for better concurrency
        "max_overflow": 10,  # Allow 10 additional connections beyond pool_size
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before using
        "pool_timeout": 30,  # Wait up to 30s for available connection
        "connect_args": {
            "timeout": 30,  # SQLite connection timeout
            "check_same_thread": False,  # Allow multi-threaded access
            "isolation_level": None,  # Autocommit mode for better performance
        },
    }

    # Echo SQL queries in development
    if settings.environment == "development" and settings.database_echo:
        engine_options["echo"] = True

    engine = create_engine(database_uri, **engine_options)

    # Create scoped session
    session_factory = sessionmaker(bind=engine)
    db_session = scoped_session(session_factory)

    # Add teardown handler to remove session after request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if db_session:
            db_session.remove()

    return engine


def init_db(app: Flask, create_tables=True):
    """
    Initialize the database with the Flask application.

    Args:
        app (Flask): Flask application instance
        create_tables (bool): Whether to create tables if they don't exist

    Returns:
        Engine: SQLAlchemy engine
    """
    engine = configure_database(app)

    if create_tables:
        with app.app_context():
            # Import all models to ensure they're registered
            from src.models import Aggregation, Annotation, File, Variant, Workspace  # noqa: F401
            from src.models.base import Base

            # Create all tables
            Base.metadata.create_all(bind=engine)

            print(f"Database initialized at: {app.config['SQLALCHEMY_DATABASE_URI']}")

    return engine


def get_db_session():
    """
    Get the current database session.

    Returns:
        Session: SQLAlchemy database session
    """
    return db_session


def reset_database(app: Flask):
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data!

    Args:
        app (Flask): Flask application instance
    """
    with app.app_context():
        from sqlalchemy import create_engine

        from src.models.base import Base

        database_uri = get_database_uri()
        engine = create_engine(database_uri)

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("Database reset complete!")
