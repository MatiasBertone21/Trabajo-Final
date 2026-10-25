"""
Pytest configuration and shared fixtures for vision-service tests.
Pure HTTP fixtures that do not import internal app dependencies on the host.
"""
import os
import pytest


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Resolve base URL for the vision-service API from environment."""
    return os.getenv("VISION_API_URL", "http://localhost:8001/api/vision").rstrip("/")
