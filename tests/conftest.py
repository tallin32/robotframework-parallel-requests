"""Pytest configuration and fixtures."""
import pytest


@pytest.fixture
def cleanup():
    """Cleanup fixture for test teardown."""
    yield
    # Any cleanup code here
