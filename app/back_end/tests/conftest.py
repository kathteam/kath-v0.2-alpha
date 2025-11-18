"""
Pytest configuration and shared fixtures for KATH backend tests.

This module provides:
- Flask app fixtures
- Database fixtures
- Mock data fixtures
- Test utilities
"""

import os

# Add src to path for imports
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import create_app
from src.config import Env
from src.models.base import Base
from src.database.config import get_db_session


@pytest.fixture(scope="session")
def app():
    """
    Create Flask application for testing.

    Scope: session (created once per test session)
    """
    # Set test environment variables
    os.environ["FLASK_ENV"] = "testing"
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce log noise in tests
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use separate Redis DB

    app = create_app()
    app.config["TESTING"] = True

    # Create database tables for integration tests
    with app.app_context():
        try:
            engine = get_db_session().get_bind()
            Base.metadata.create_all(engine)
        except Exception:
            # If we can't create tables, tests will fail gracefully
            pass

    yield app


@pytest.fixture(scope="function")
def client(app):
    """
    Create Flask test client.

    Scope: function (new client for each test)
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """
    Create Flask CLI runner.

    Scope: function (new runner for each test)
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def temp_workspace(tmp_path):
    """
    Create temporary workspace directory with test files.

    Returns:
        Path: Temporary workspace directory
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create subdirectories
    (workspace / "data").mkdir()
    (workspace / "results").mkdir()

    yield workspace


@pytest.fixture(scope="function")
def sample_csv_file(temp_workspace):
    """
    Create sample CSV file for testing.

    Returns:
        Path: Path to sample CSV file
    """
    csv_path = temp_workspace / "data" / "sample.csv"

    # Create sample data
    df = pd.DataFrame(
        {
            "chromosome": ["chr1", "chr1", "chr2", "chr2", "chr3"],
            "position": [12345, 67890, 11111, 22222, 33333],
            "ref": ["A", "G", "C", "T", "A"],
            "alt": ["T", "C", "G", "A", "G"],
            "gene": ["BRCA1", "BRCA1", "TP53", "TP53", "EGFR"],
        }
    )

    df.to_csv(csv_path, index=False)

    return csv_path


@pytest.fixture(scope="function")
def large_csv_file(temp_workspace):
    """
    Create large CSV file for pagination testing.

    Returns:
        Path: Path to large CSV file
    """
    csv_path = temp_workspace / "data" / "large.csv"

    # Create 1000 rows
    data = {
        "chromosome": [f"chr{i % 23}" for i in range(1000)],
        "position": [i * 1000 for i in range(1000)],
        "ref": ["A"] * 1000,
        "alt": ["T"] * 1000,
    }

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)

    return csv_path


@pytest.fixture(scope="function")
def mock_variant():
    """
    Create mock variant data.

    Returns:
        dict: Mock variant data
    """
    return {
        "chromosome": "chr1",
        "position": 12345,
        "ref": "A",
        "alt": "T",
        "gene": "BRCA1",
        "transcript": "NM_007294.3",
    }


@pytest.fixture(scope="function")
def mock_variants():
    """
    Create list of mock variants.

    Returns:
        list: List of mock variant dicts
    """
    return [
        {"chromosome": "chr1", "position": 12345, "ref": "A", "alt": "T", "gene": "BRCA1"},
        {"chromosome": "chr1", "position": 67890, "ref": "G", "alt": "C", "gene": "BRCA2"},
        {"chromosome": "chr2", "position": 11111, "ref": "C", "alt": "G", "gene": "TP53"},
    ]


@pytest.fixture(scope="function")
def mock_request_headers():
    """
    Create mock request headers.

    Returns:
        dict: Request headers
    """
    return {
        "uuid": "test-uuid-1234",
        "sid": "test-session-5678",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="function")
def mock_socketio():
    """
    Create mock Socket.IO instance.

    Returns:
        Mock: Mock Socket.IO object
    """
    socketio = MagicMock()
    socketio.emit = MagicMock()
    return socketio


@pytest.fixture(scope="function")
def mock_redis():
    """
    Create mock Redis client.

    Returns:
        Mock: Mock Redis client
    """
    redis_client = MagicMock()
    redis_client.get = MagicMock(return_value=None)
    redis_client.set = MagicMock(return_value=True)
    redis_client.delete = MagicMock(return_value=True)
    redis_client.smembers = MagicMock(return_value=set())
    redis_client.sadd = MagicMock(return_value=True)
    redis_client.srem = MagicMock(return_value=True)
    return redis_client


@pytest.fixture(scope="function")
def mock_pandas_dataframe():
    """
    Create mock pandas DataFrame.

    Returns:
        DataFrame: Mock DataFrame with variant data
    """
    return pd.DataFrame(
        {
            "chromosome": ["chr1", "chr1", "chr2"],
            "position": [12345, 67890, 11111],
            "ref": ["A", "G", "C"],
            "alt": ["T", "C", "G"],
            "gene": ["BRCA1", "BRCA2", "TP53"],
        }
    )


# Test utilities


def assert_valid_json_response(response, status_code=200):
    """
    Assert that response is valid JSON with correct status code.

    Args:
        response: Flask response object
        status_code: Expected status code
    """
    assert response.status_code == status_code
    assert response.content_type == "application/json"
    return response.get_json()


def assert_error_response(response, status_code, error_message_contains=None):
    """
    Assert that response is an error with expected message.

    Args:
        response: Flask response object
        status_code: Expected status code
        error_message_contains: Substring expected in error message
    """
    assert response.status_code == status_code
    data = response.get_json()
    assert "error" in data or "message" in data

    if error_message_contains:
        error_msg = data.get("error", data.get("message", ""))
        assert error_message_contains in error_msg


def create_mock_file_tree():
    """
    Create mock file tree structure for testing.

    Returns:
        list: Mock file tree
    """
    return [
        {"id": "file1.csv", "label": "file1.csv", "type": "csv", "children": None},
        {
            "id": "folder1",
            "label": "folder1",
            "type": "folder",
            "children": [{"id": "folder1/file2.csv", "label": "file2.csv", "type": "csv", "children": None}],
        },
    ]


# Markers helpers


def requires_redis(func):
    """
    Decorator to skip test if Redis is not available.
    """
    import pytest

    def check_redis():
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=15)
            r.ping()
            return True
        except:
            return False

    return pytest.mark.skipif(not check_redis(), reason="Redis not available")(func)


def requires_file(file_path):
    """
    Decorator to skip test if required file is not present.
    """
    import pytest

    return pytest.mark.skipif(not Path(file_path).exists(), reason=f"Required file not found: {file_path}")
