"""
Application configuration using pydantic-settings for type-safe, validated configuration.

This module provides:
- Type-safe configuration objects
- Automatic environment variable loading
- Configuration validation on startup
- Environment-specific settings (development, production, testing)
- YAML-based network configuration loading

Usage:
    from src.settings import get_settings

    settings = get_settings()
    print(settings.flask_host, settings.flask_port)
"""

import os
import sys
from functools import lru_cache
from typing import Any, List, Literal, Optional, Union

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import configuration loader for YAML-based settings
try:
    from src.config_loader import load_network_config as yaml_load_config
    from src.config_loader import merge_with_environment as yaml_merge_config
except ImportError:
    # Fallback if config_loader is not available
    yaml_load_config = None  # type: ignore
    yaml_merge_config = None  # type: ignore


class AppSettings(BaseSettings):
    """
    Application settings with validation and type safety.

    All settings are loaded from environment variables.
    Default values are provided for development convenience.
    """

    # Environment configuration
    environment: Literal["development", "production", "testing"] = Field(
        default="development", description="Application environment", validation_alias="ENVIRONMENT"
    )

    # Flask configuration
    flask_host: str = Field(
        default="0.0.0.0", description="Flask server host address", validation_alias="FLASK_RUN_HOST"
    )

    flask_port: int = Field(
        default=8080, ge=1, le=65535, description="Flask server port number", validation_alias="FLASK_RUN_PORT"
    )

    flask_env: str = Field(default="development", description="Flask environment mode", validation_alias="FLASK_ENV")

    flask_debug: bool = Field(default=False, description="Enable Flask debug mode", validation_alias="FLASK_DEBUG")

    # CORS configuration
    cors_origins: Union[str, List[str]] = Field(
        default="*", description="Allowed CORS origins (comma-separated string or list)", validation_alias="ORIGINS"
    )

    # Redis configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL", validation_alias="REDIS_URL"
    )

    # Processing limits
    max_entries: int = Field(
        default=sys.maxsize,
        ge=1,
        description="Maximum number of entries to process (for SpliceAI and CADD)",
        validation_alias="MAX_ENTRIES",
    )

    # CUDA configuration
    use_cuda: bool = Field(default=False, description="Enable CUDA for SpliceAI processing", validation_alias="CUDA")

    cuda_batch_size: int = Field(
        default=32, ge=1, le=1024, description="Batch size for CUDA processing", validation_alias="CUDA_BATCH_SIZE"
    )

    # Logging configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level", validation_alias="LOG_LEVEL"
    )

    log_dir: str = Field(default="logs", description="Directory for log files", validation_alias="LOG_DIR")

    # Domain configuration
    domain: str = Field(default="localhost", description="Application domain", validation_alias="DOMAIN")

    # Database configuration
    database_path: str = Field(
        default="instance/kath.db", description="SQLite database file path", validation_alias="DATABASE_PATH"
    )

    database_echo: bool = Field(
        default=False, description="Echo SQL queries (debug mode)", validation_alias="DATABASE_ECHO"
    )

    use_database_backend: bool = Field(
        default=True,
        description="Use database for variant data instead of CSV files",
        validation_alias="USE_DATABASE_BACKEND",
    )

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env.development",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        # Handle single value
        return [str(v)]

    @field_validator("use_cuda", mode="before")
    @classmethod
    def parse_boolean(cls, v):
        """Parse boolean from string values."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    def get_env_file(self) -> str:
        """Get the appropriate .env file based on environment."""
        env_files = {
            "production": ".env.production",
            "development": ".env.development",
            "testing": ".env.testing",
        }
        return env_files.get(self.environment, ".env.development")

    @classmethod
    def _extract_backend_config(cls, yaml_config: dict[str, Any]) -> dict[str, Any]:
        """Extract backend configuration from YAML."""
        kwargs: dict[str, Any] = {}
        if yaml_config.get("backend"):
            backend = yaml_config["backend"]
            if "host" in backend:
                kwargs["flask_host"] = backend["host"]
            if "port" in backend:
                kwargs["flask_port"] = backend["port"]
            if "domain" in backend:
                kwargs["domain"] = backend["domain"]
        return kwargs

    @classmethod
    def _extract_cors_config(cls, yaml_config: dict[str, Any]) -> dict[str, Any]:
        """Extract CORS configuration from YAML."""
        kwargs: dict[str, Any] = {}
        if yaml_config.get("cors"):
            cors = yaml_config["cors"]
            if "allowed_origins" in cors:
                kwargs["cors_origins"] = cors["allowed_origins"]
        return kwargs

    @classmethod
    def _extract_redis_config(cls, yaml_config: dict[str, Any]) -> dict[str, Any]:
        """Extract Redis configuration from YAML."""
        kwargs: dict[str, Any] = {}
        if yaml_config.get("redis"):
            redis = yaml_config["redis"]
            host = redis.get("host", "localhost")
            port = redis.get("port", 6379)
            db = redis.get("database", 0)
            kwargs["redis_url"] = f"redis://{host}:{port}/{db}"
        return kwargs

    @classmethod
    def load_from_yaml(cls) -> "AppSettings":
        """
        Load settings from YAML configuration file.

        Loads network configuration from network_config.yaml and merges with
        environment variables. Environment variables take precedence.

        Returns:
            AppSettings: Settings instance with values from YAML and environment
        """
        if yaml_load_config is None:
            return cls()

        try:
            yaml_config = yaml_load_config()
            kwargs: dict[str, Any] = {}

            # Extract settings from YAML
            kwargs.update(cls._extract_backend_config(yaml_config))
            kwargs.update(cls._extract_cors_config(yaml_config))
            kwargs.update(cls._extract_redis_config(yaml_config))

            return cls(**kwargs)
        except Exception as e:
            # If YAML loading fails, fall back to standard loading
            print(f"Warning: Failed to load YAML config: {e}. Using environment variables only.")
            return cls()


class DevelopmentSettings(AppSettings):
    """Development-specific settings with debug enabled."""

    flask_debug: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=".env.development",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class ProductionSettings(AppSettings):
    """Production-specific settings with stricter defaults."""

    flask_debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env.production",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class TestingSettings(AppSettings):
    """Testing-specific settings."""

    flask_env: str = "testing"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "ERROR"
    redis_url: str = "redis://localhost:6379/15"  # Separate Redis DB for tests

    model_config = SettingsConfigDict(
        env_file=".env.testing",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings(environment: Optional[str] = None) -> AppSettings:
    """
    Get application settings based on environment.

    This function is cached to ensure settings are loaded only once.
    It attempts to load configuration from network_config.yaml first,
    then falls back to environment variables.

    Args:
        environment: Optional environment override ("development", "production", "testing")
                    If not provided, uses ENVIRONMENT env variable

    Returns:
        AppSettings instance configured for the current environment

    Example:
        >>> settings = get_settings()
        >>> print(f"Running on {settings.flask_host}:{settings.flask_port}")
    """
    # Determine environment
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")

    # Return appropriate settings class
    settings_classes = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }

    settings_class = settings_classes.get(environment, DevelopmentSettings)

    # Try to load from YAML first, fall back to standard loading
    try:
        return settings_class.load_from_yaml()
    except Exception:
        # Fall back to standard environment-based loading
        return settings_class()


# Convenience function for backward compatibility with old Env class
def load_env():
    """Load environment variables from .env file."""
    settings = get_settings()
    # Settings are automatically loaded by pydantic-settings
    return settings


# Export main settings getter
__all__ = [
    "AppSettings",
    "DevelopmentSettings",
    "ProductionSettings",
    "TestingSettings",
    "get_settings",
    "load_env",
]
