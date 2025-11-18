"""
Unit tests for the pydantic-based settings module.

This module tests:
- Settings loading and validation
- Environment-specific configuration
- Type checking and validation
- Default values
- Configuration errors
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.settings import AppSettings, DevelopmentSettings, ProductionSettings, TestingSettings, get_settings


@pytest.mark.unit
class TestAppSettings:
    """Tests for base AppSettings class."""

    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        with patch.dict(os.environ, {}, clear=True):
            # Create settings without loading from .env file
            settings = AppSettings(_env_file=None)

            assert settings.environment == "development"
            assert settings.flask_host == "0.0.0.0"
            assert settings.flask_port == 8080
            assert settings.cors_origins == ["*"]
            assert settings.redis_url == "redis://localhost:6379/0"
            assert settings.use_cuda is False
            assert settings.cuda_batch_size == 32

    def test_settings_from_env_variables(self):
        """Test loading settings from environment variables."""
        with patch.dict(
            os.environ,
            {
                "FLASK_RUN_HOST": "127.0.0.1",
                "FLASK_RUN_PORT": "5000",
                "ORIGINS": "http://localhost:3000,http://localhost:5173",
                "REDIS_URL": "redis://localhost:6379/15",
                "CUDA": "true",
                "CUDA_BATCH_SIZE": "64",
            },
            clear=True,
        ):
            settings = AppSettings(_env_file=None)

            assert settings.flask_host == "127.0.0.1"
            assert settings.flask_port == 5000
            assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]
            assert settings.redis_url == "redis://localhost:6379/15"
            assert settings.use_cuda is True
            assert settings.cuda_batch_size == 64

    def test_port_validation_valid(self):
        """Test that valid port numbers are accepted."""
        with patch.dict(os.environ, {"FLASK_RUN_PORT": "8080"}, clear=True):
            settings = AppSettings(_env_file=None)
            assert settings.flask_port == 8080

    def test_port_validation_invalid_too_low(self):
        """Test that port number below 1 is rejected."""
        with patch.dict(os.environ, {"FLASK_RUN_PORT": "0"}, clear=True):
            with pytest.raises(ValidationError) as excinfo:
                AppSettings(_env_file=None)

            assert "greater than or equal to 1" in str(excinfo.value)

    def test_port_validation_invalid_too_high(self):
        """Test that port number above 65535 is rejected."""
        with patch.dict(os.environ, {"FLASK_RUN_PORT": "65536"}, clear=True):
            with pytest.raises(ValidationError) as excinfo:
                AppSettings(_env_file=None)

            assert "less than or equal to 65535" in str(excinfo.value)

    def test_port_validation_invalid_type(self):
        """Test that non-integer port is rejected."""
        with patch.dict(os.environ, {"FLASK_RUN_PORT": "not_a_number"}, clear=True):
            with pytest.raises(ValidationError) as excinfo:
                AppSettings(_env_file=None)

            assert "Input should be a valid integer" in str(excinfo.value)

    def test_cuda_batch_size_validation(self):
        """Test CUDA batch size validation."""
        # Valid batch size
        with patch.dict(os.environ, {"CUDA_BATCH_SIZE": "128"}, clear=True):
            settings = AppSettings(_env_file=None)
            assert settings.cuda_batch_size == 128

        # Invalid: too low
        with patch.dict(os.environ, {"CUDA_BATCH_SIZE": "0"}, clear=True):
            with pytest.raises(ValidationError):
                AppSettings(_env_file=None)

        # Invalid: too high
        with patch.dict(os.environ, {"CUDA_BATCH_SIZE": "2048"}, clear=True):
            with pytest.raises(ValidationError):
                AppSettings(_env_file=None)

    def test_boolean_parsing(self):
        """Test parsing of boolean values from strings."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"CUDA": env_value}, clear=True):
                settings = AppSettings(_env_file=None)
                assert settings.use_cuda == expected, f"Failed for {env_value}"

    def test_cors_origins_parsing_single(self):
        """Test parsing single CORS origin."""
        with patch.dict(os.environ, {"ORIGINS": "http://localhost:3000"}, clear=True):
            settings = AppSettings(_env_file=None)
            assert settings.cors_origins == ["http://localhost:3000"]

    def test_cors_origins_parsing_multiple(self):
        """Test parsing multiple CORS origins."""
        with patch.dict(
            os.environ, {"ORIGINS": "http://localhost:3000, http://localhost:5173, https://example.com"}, clear=True
        ):
            settings = AppSettings(_env_file=None)
            assert len(settings.cors_origins) == 3
            assert "http://localhost:3000" in settings.cors_origins
            assert "http://localhost:5173" in settings.cors_origins
            assert "https://example.com" in settings.cors_origins

    def test_cors_origins_whitespace_handling(self):
        """Test that whitespace is properly stripped from CORS origins."""
        with patch.dict(os.environ, {"ORIGINS": "  http://localhost:3000  ,   http://localhost:5173  "}, clear=True):
            settings = AppSettings(_env_file=None)
            assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]

    def test_log_level_validation(self):
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            with patch.dict(os.environ, {"LOG_LEVEL": level}, clear=True):
                settings = AppSettings(_env_file=None)
                assert settings.log_level == level

        # Invalid log level
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True):
            with pytest.raises(ValidationError) as excinfo:
                AppSettings(_env_file=None)

            assert "Input should be" in str(excinfo.value)

    def test_max_entries_validation(self):
        """Test max entries validation."""
        with patch.dict(os.environ, {"MAX_ENTRIES": "1000"}, clear=True):
            settings = AppSettings(_env_file=None)
            assert settings.max_entries == 1000

        # Invalid: must be positive
        with patch.dict(os.environ, {"MAX_ENTRIES": "0"}, clear=True):
            with pytest.raises(ValidationError):
                AppSettings(_env_file=None)


@pytest.mark.unit
class TestEnvironmentSpecificSettings:
    """Tests for environment-specific settings classes."""

    def test_development_settings(self):
        """Test development-specific settings."""
        with patch.dict(os.environ, {}, clear=True):
            settings = DevelopmentSettings(_env_file=None)

            assert settings.flask_debug is True
            assert settings.log_level == "DEBUG"

    def test_production_settings(self):
        """Test production-specific settings."""
        with patch.dict(os.environ, {}, clear=True):
            settings = ProductionSettings(_env_file=None)

            assert settings.flask_debug is False
            assert settings.log_level == "INFO"

    def test_testing_settings(self):
        """Test testing-specific settings."""
        with patch.dict(os.environ, {}, clear=True):
            settings = TestingSettings(_env_file=None)

            assert settings.flask_env == "testing"
            assert settings.log_level == "ERROR"
            assert settings.redis_url == "redis://localhost:6379/15"


@pytest.mark.unit
class TestGetSettings:
    """Tests for get_settings() function."""

    def test_get_settings_development(self):
        """Test getting development settings."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            # Clear cache
            get_settings.cache_clear()

            settings = get_settings()

            assert isinstance(settings, DevelopmentSettings)
            assert settings.flask_debug is True

    def test_get_settings_production(self):
        """Test getting production settings."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            # Clear cache
            get_settings.cache_clear()

            settings = get_settings()

            assert isinstance(settings, ProductionSettings)
            assert settings.flask_debug is False

    def test_get_settings_testing(self):
        """Test getting testing settings."""
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}, clear=True):
            # Clear cache
            get_settings.cache_clear()

            settings = get_settings()

            assert isinstance(settings, TestingSettings)
            assert settings.flask_env == "testing"

    def test_get_settings_caching(self):
        """Test that settings are cached."""
        get_settings.cache_clear()

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()

            # Should return the same instance
            assert settings1 is settings2

    def test_get_settings_explicit_environment(self):
        """Test explicitly specifying environment."""
        get_settings.cache_clear()

        settings = get_settings(environment="production")

        assert isinstance(settings, ProductionSettings)


@pytest.mark.unit
class TestBackwardCompatibility:
    """Tests for backward compatibility with old Env class."""

    def test_env_class_still_works(self):
        """Test that old Env class interface still works."""
        from src.config import Env

        # These should not raise errors
        host = Env.get_flask_run_host()
        port = Env.get_flask_run_port()
        origins = Env.get_origins()
        redis_url = Env.get_redis_url()
        max_entries = Env.get_max_entries()
        use_cuda = Env.get_use_cuda()
        cuda_batch_size = Env.get_cuda_batch_size()

        # Check types
        assert isinstance(host, str)
        assert isinstance(port, int)
        assert isinstance(origins, list)
        assert isinstance(redis_url, str)
        assert isinstance(max_entries, int)
        assert isinstance(use_cuda, bool)
        assert isinstance(cuda_batch_size, int)
