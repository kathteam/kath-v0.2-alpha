"""
Backward compatibility shim for old Env class.

This module provides the old Env interface using the new settings system.
All new code should use src.settings.get_settings() directly.
"""

from typing import List, Union

from src.settings import get_settings

# Get settings instance
_settings = get_settings()


class Env:
    """
    Backward-compatible Env class using new settings system.

    DEPRECATED: This class exists only for backward compatibility.
    New code should use get_settings() from src.settings instead.

    Example migration:
        # Old
        from src.config import Env
        port = Env.get_flask_run_port()

        # New
        from src.settings import get_settings
        settings = get_settings()
        port = settings.flask_port
    """

    @classmethod
    def load_env(cls):
        """Load environment variables (no-op with pydantic-settings)."""
        # Settings are automatically loaded by pydantic-settings
        pass

    @classmethod
    def get_flask_run_host(cls) -> str:
        """Get the Flask server host from environment variables."""
        return _settings.flask_host

    @classmethod
    def get_flask_run_port(cls) -> int:
        """Get the Flask server port from environment variables."""
        return _settings.flask_port

    @classmethod
    def get_origins(cls) -> Union[str, List[str]]:
        """Get the list of allowed origins for CORS from environment variables."""
        return _settings.cors_origins

    @classmethod
    def get_redis_url(cls) -> str:
        """Get the Redis URL from environment variables."""
        return _settings.redis_url

    @classmethod
    def get_max_entries(cls) -> int:
        """Get the maximum number of entries to process from environment variables."""
        return _settings.max_entries

    @classmethod
    def get_use_cuda(cls) -> bool:
        """Check whether CUDA should be used for SpliceAI."""
        return _settings.use_cuda

    @classmethod
    def get_cuda_batch_size(cls) -> int:
        """Get the CUDA batch size for SpliceAI."""
        return _settings.cuda_batch_size


# Export for backward compatibility
__all__ = ["Env"]
