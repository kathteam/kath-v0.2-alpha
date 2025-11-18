"""
Tests package for KATH backend.

This package contains all unit and integration tests.
"""

# Workaround for pytest-asyncio 0.23.3 bug with Package collectors
# We don't use async tests, so we don't need the package-level event loop fixture
