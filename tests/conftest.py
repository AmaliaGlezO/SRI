"""Pytest configuration and fixtures."""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Create test directories if they don't exist
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment."""
    required_dirs = [
        Path("data"),
        Path("logs"),
        Path("models"),
        Path("indexes"),
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield



@pytest.fixture(scope="function")
def temp_data_dir(tmp_path):
    """Provide a temporary data directory for tests."""
    return tmp_path / "data"


@pytest.fixture(scope="function")
def test_query():
    """Provide a test query."""
    return "¿Que modelos de moviles hay de samsung en 2026? pensará en sacar algunos nuevos en 2027?"


@pytest.fixture(scope="function")
def test_document():
    """Provide a test document."""
    return {
        "title": "Test Document",
        "content": "This is a test document about AI.",
        "url": "http://example.com/test",
        "source": "test",
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as requiring Docker"
    )
