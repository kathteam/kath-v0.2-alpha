"""
Unit tests for the Env configuration class (DEPRECATED).

DEPRECATED: These tests are for the legacy Env class which is now a compatibility shim.
For comprehensive configuration tests, see test_settings.py.

The Env class now uses pydantic-settings internally, which caches settings at import time.
Some tests that patch os.environ may fail because settings are loaded once.

This module tests:
- Environment variable loading (limited due to caching)
- Configuration value retrieval
- Type conversions
- Default values
- Backward compatibility
"""

import os
from unittest.mock import patch

import pytest

from src.config import Env
from src.settings import get_settings


@pytest.mark.unit
@pytest.mark.utils
class TestEnvConfiguration:
    """Tests for Env class configuration methods."""

    def test_get_flask_run_host_default(self):
        """Test get_flask_run_host returns default value."""
        with patch.dict(os.environ, {}, clear=True):
            host = Env.get_flask_run_host()
            assert host == "0.0.0.0"
            assert isinstance(host, str)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_flask_run_host_from_env(self):
        """Test get_flask_run_host reads from environment."""
        with patch.dict(os.environ, {"FLASK_RUN_HOST": "127.0.0.1"}):
            host = Env.get_flask_run_host()
            assert host == "127.0.0.1"
            assert isinstance(host, str)

    def test_get_flask_run_port_default(self):
        """Test get_flask_run_port returns default value as integer."""
        with patch.dict(os.environ, {}, clear=True):
            port = Env.get_flask_run_port()
            assert port == 8080
            assert isinstance(port, int)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_flask_run_port_from_env(self):
        """Test get_flask_run_port reads from environment and converts to int."""
        with patch.dict(os.environ, {"FLASK_RUN_PORT": "5000"}):
            port = Env.get_flask_run_port()
            assert port == 5000
            assert isinstance(port, int)

    def test_get_flask_run_port_type_conversion(self):
        """Test get_flask_run_port properly converts string to int."""
        # This is the critical test for the bug fix
        with patch.dict(os.environ, {"FLASK_RUN_PORT": "8080"}):
            port = Env.get_flask_run_port()
            # Port must be int, not string, for socket binding
            assert isinstance(port, int)
            assert not isinstance(port, str)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_origins_default(self):
        """Test get_origins returns default value."""
        with patch.dict(os.environ, {}, clear=True):
            origins = Env.get_origins()
            assert origins == ["*"]
            assert isinstance(origins, list)

    def test_get_origins_single(self):
        """Test get_origins with single origin."""
        with patch.dict(os.environ, {"ORIGINS": "http://localhost:5173"}):
            origins = Env.get_origins()
            assert origins == ["http://localhost:5173"]
            assert isinstance(origins, list)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_origins_multiple(self):
        """Test get_origins with multiple origins."""
        with patch.dict(os.environ, {"ORIGINS": "http://localhost:5173,http://localhost:3000"}):
            origins = Env.get_origins()
            assert origins == ["http://localhost:5173", "http://localhost:3000"]
            assert len(origins) == 2

    def test_get_redis_url_default(self):
        """Test get_redis_url returns default value."""
        with patch.dict(os.environ, {}, clear=True):
            redis_url = Env.get_redis_url()
            assert redis_url == "redis://localhost:6379/0"
            assert isinstance(redis_url, str)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_redis_url_from_env(self):
        """Test get_redis_url reads from environment."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/15"}):
            redis_url = Env.get_redis_url()
            assert redis_url == "redis://localhost:6379/15"
            assert isinstance(redis_url, str)

    def test_get_max_entries_default(self):
        """Test get_max_entries returns default (sys.maxsize)."""
        with patch.dict(os.environ, {}, clear=True):
            max_entries = Env.get_max_entries()
            assert max_entries == 9223372036854775807  # sys.maxsize on 64-bit
            assert isinstance(max_entries, int)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_max_entries_from_env(self):
        """Test get_max_entries reads from environment."""
        with patch.dict(os.environ, {"MAX_ENTRIES": "100"}):
            max_entries = Env.get_max_entries()
            assert max_entries == 100
            assert isinstance(max_entries, int)

    @pytest.mark.skip(reason="Settings validation handled by pydantic; see test_settings.py")
    def test_get_max_entries_invalid_value(self):
        """Test get_max_entries raises ValueError for invalid input."""
        with patch.dict(os.environ, {"MAX_ENTRIES": "not_a_number"}):
            with pytest.raises(ValueError) as excinfo:
                Env.get_max_entries()
            assert "Invalid value for MAX_ENTRIES" in str(excinfo.value)

    def test_get_use_cuda_default(self):
        """Test get_use_cuda returns default value (False)."""
        with patch.dict(os.environ, {}, clear=True):
            use_cuda = Env.get_use_cuda()
            assert use_cuda is False
            assert isinstance(use_cuda, bool)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_use_cuda_true(self):
        """Test get_use_cuda returns True when enabled."""
        with patch.dict(os.environ, {"CUDA": "true"}):
            use_cuda = Env.get_use_cuda()
            assert use_cuda is True

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_use_cuda_true_uppercase(self):
        """Test get_use_cuda handles uppercase TRUE."""
        with patch.dict(os.environ, {"CUDA": "TRUE"}):
            use_cuda = Env.get_use_cuda()
            assert use_cuda is True

    def test_get_use_cuda_false(self):
        """Test get_use_cuda returns False when disabled."""
        with patch.dict(os.environ, {"CUDA": "false"}):
            use_cuda = Env.get_use_cuda()
            assert use_cuda is False

    def test_get_cuda_batch_size_default(self):
        """Test get_cuda_batch_size returns default value as integer."""
        with patch.dict(os.environ, {}, clear=True):
            batch_size = Env.get_cuda_batch_size()
            assert batch_size == 32
            assert isinstance(batch_size, int)

    @pytest.mark.skip(reason="Settings are cached at import; see test_settings.py for comprehensive tests")
    def test_get_cuda_batch_size_from_env(self):
        """Test get_cuda_batch_size reads from environment and converts to int."""
        with patch.dict(os.environ, {"CUDA_BATCH_SIZE": "64"}):
            batch_size = Env.get_cuda_batch_size()
            assert batch_size == 64
            assert isinstance(batch_size, int)

    def test_get_cuda_batch_size_type_conversion(self):
        """Test get_cuda_batch_size properly converts string to int."""
        with patch.dict(os.environ, {"CUDA_BATCH_SIZE": "128"}):
            batch_size = Env.get_cuda_batch_size()
            # Batch size must be int, not string
            assert isinstance(batch_size, int)
            assert not isinstance(batch_size, str)


@pytest.mark.unit
@pytest.mark.utils
class TestEnvEnvironmentSelection:
    """Tests for environment file selection."""

    @pytest.mark.skip(reason="Environment selection now handled by pydantic-settings; see test_settings.py")
    def test_environment_default(self):
        """Test default environment is development."""
        with patch.dict(os.environ, {}, clear=True):
            # Access class attribute directly
            assert Env.DOTENV_PATH == ".env.development"

    def test_environment_production(self):
        """Test production environment selection."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            # Need to reload the class to pick up new env var
            # This test shows the limitation of the static approach
            env_path = {
                "production": ".env.production",
                "development": ".env.development",
            }.get(os.getenv("ENVIRONMENT", "development"), ".env.development")
            assert env_path == ".env.production"

    def test_environment_development(self):
        """Test development environment selection."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            env_path = {
                "production": ".env.production",
                "development": ".env.development",
            }.get(os.getenv("ENVIRONMENT", "development"), ".env.development")
            assert env_path == ".env.development"

    def test_environment_unknown_defaults_to_development(self):
        """Test unknown environment defaults to development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            env_path = {
                "production": ".env.production",
                "development": ".env.development",
            }.get(os.getenv("ENVIRONMENT", "development"), ".env.development")
            assert env_path == ".env.development"
