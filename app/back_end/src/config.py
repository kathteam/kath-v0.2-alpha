"""
This module defines the `Env` class, which handles environment configuration for the application.

The class manages:
- Loading environment variables from a `.env` file based on the application's environment.
- Retrieving specific environment variables with default fallbacks.
- Providing configuration values for the Flask server, such as host, port, and allowed origins.

Dependencies:
- os: Used for interacting with the operating system to retrieve environment variables.
- dotenv: Used for loading environment variables from a `.env` file.
"""

# pylint: disable=import-error

import os
import sys
from dotenv import load_dotenv


class Env:
    """Handles environment configuration and retrieval of environment-specific settings."""

    # Determine the current environment and select the appropriate .env file
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DOTENV_PATH = {
        "production": ".env.production",
        "development": ".env.development",
    }.get(ENVIRONMENT, ".env.development")

    @classmethod
    def load_env(cls):
        """
        Load environment variables from the appropriate .env file.

        This method uses the `python-dotenv` package to load the environment variables
        from the `.env` file corresponding to the current environment (development or production).
        """
        load_dotenv(cls.DOTENV_PATH)

    @classmethod
    def get_flask_run_host(cls):
        """
        Get the Flask server host from environment variables.

        This is typically used to define the host on which the Flask app will run.

        Returns:
            str: The host address, defaulting to "0.0.0.0".
        """
        return os.getenv("FLASK_RUN_HOST", "0.0.0.0")

    @classmethod
    def get_flask_run_port(cls):
        """
        Get the Flask server port from environment variables.

        This is used to define the port on which the Flask app will run.

        Returns:
            int: The port number, defaulting to 8080.
        """
        return os.getenv("FLASK_RUN_PORT", 8080)

    @classmethod
    def get_origins(cls):
        """
        Get the list of allowed origins for CORS from environment variables.

        This is used for configuring CORS policies in the Flask app.

        Returns:
            list: A list of origins allowed for CORS, defaulting to ["*"].
        """
        origins = os.getenv("ORIGINS", "*")
        return origins.split(",")

    @classmethod
    def get_redis_url(cls):
        """
        Get the Redis URL from environment variables.

        This is used for connecting to the Redis server.

        Returns:
            str: The Redis URL, defaulting to "redis://localhost:6379/0".
        """
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")

    @classmethod
    def get_max_entries(cls):
        """
        Get the maximum number of entries to process from environment variables. Works on spliceai and cadd.

        This is used to limit the number of entries to process when testing.

        Returns:
            int: The maximum number of entries to process, or sys.maxsize if no limit.
        """
        try:
            return int(os.getenv("MAX_ENTRIES", str(sys.maxsize)))
        except ValueError as e:
            raise ValueError(f"Invalid value for MAX_ENTRIES: {os.getenv('MAX_ENTRIES')}. It must be an integer or unset.") from e

    @classmethod
    def get_use_cuda(cls):
        """
        Check whether CUDA should be used for SpliceAI.

        Returns:
            bool: True if CUDA is enabled, False otherwise.
        """
        return os.getenv("CUDA", "false").lower() == "true"

    @classmethod
    def get_cuda_batch_size(cls):
        """
        Get the CUDA batch size for SpliceAI.

        Returns:
            str: Batch size, defaulting to "32".
        """
        return os.getenv("CUDA_BATCH_SIZE", "32")

