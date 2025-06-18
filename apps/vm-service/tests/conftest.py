"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)