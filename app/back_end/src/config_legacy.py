"""
DEPRECATED: Legacy Env class for backward compatibility.

This module is deprecated and will be removed in v0.4.
Please use src.settings.get_settings() instead.

Migration guide:
    # Old way
    from src.config import Env
    host = Env.get_flask_run_host()
    port = Env.get_flask_run_port()

    # New way
    from src.settings import get_settings
    settings = get_settings()
    host = settings.flask_host
    port = settings.flask_port
"""

import os
import sys
import warnings

from dotenv import load_dotenv


class Env:
    """
    DEPRECATED: Legacy environment configuration class.

    This class is maintained for backward compatibility only.
    Use src.settings.get_settings() for new code.
    """

    # Determine the current environment and select the appropriate .env file
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DOTENV_PATH = {
        "production": ".env.production",
        "development": ".env.development",
    }.get(ENVIRONMENT, ".env.development")

    @classmethod
    def load_env(cls):
        """Load environment variables from the appropriate .env file."""
        warnings.warn(
            "Env.load_env() is deprecated. Use get_settings() from src.settings instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        load_dotenv(cls.DOTENV_PATH)

    @classmethod
    def get_flask_run_host(cls):
        """Get the Flask server host from environment variables."""
        return os.getenv("FLASK_RUN_HOST", "0.0.0.0")

    @classmethod
    def get_flask_run_port(cls):
        """Get the Flask server port from environment variables."""
        port = os.getenv("FLASK_RUN_PORT", "8080")
        return int(port)

    @classmethod
    def get_origins(cls):
        """Get the list of allowed origins for CORS from environment variables."""
        origins = os.getenv("ORIGINS", "*")
        return origins.split(",")

    @classmethod
    def get_redis_url(cls):
        """Get the Redis URL from environment variables."""
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")

    @classmethod
    def get_max_entries(cls):
        """Get the maximum number of entries to process from environment variables."""
        try:
            return int(os.getenv("MAX_ENTRIES", str(sys.maxsize)))
        except ValueError as e:
            raise ValueError(
                f"Invalid value for MAX_ENTRIES: {os.getenv('MAX_ENTRIES')}. It must be an integer or unset."
            ) from e

    @classmethod
    def get_use_cuda(cls):
        """Check whether CUDA should be used for SpliceAI."""
        return os.getenv("CUDA", "false").lower() == "true"

    @classmethod
    def get_cuda_batch_size(cls):
        """Get the CUDA batch size for SpliceAI."""
        batch_size = os.getenv("CUDA_BATCH_SIZE", "32")
        return int(batch_size)
