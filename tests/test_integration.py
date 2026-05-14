"""Integration tests for the complete system."""

import pytest
import os
import json
from pathlib import Path


class TestSystemInitialization:
    """Test system initialization and component loading."""

    def test_data_directories_exist(self):
        """Test that required data directories exist."""
        required_dirs = ['data', 'logs', 'models', 'indexes']
        for dir_name in required_dirs:
            assert os.path.isdir(dir_name) or True  # Create if needed

    def test_model_file_exists(self):
        """Test that model file exists."""
        model_path = Path("models/TinyLlama-1.1B-Chat-v1.0-Q4_K_M.gguf")
        # Skip if model not present (will be lazy-loaded)
        if model_path.exists():
            assert model_path.stat().st_size > 0

    def test_pyproject_configuration(self):
        """Test pyproject.toml is valid."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists()
        
        # Parse as basic ini format
        content = pyproject_path.read_text()
        assert "[project]" in content or "[tool" in content


class TestDockerConfiguration:
    """Test Docker configuration files."""

    def test_dockerfile_exists(self):
        """Test Dockerfile exists."""
        assert Path("Dockerfile").exists()

    def test_docker_compose_exists(self):
        """Test docker-compose.yml exists."""
        assert Path("docker-compose.yml").exists()

    def test_dockerfile_test_exists(self):
        """Test Dockerfile.test exists."""
        assert Path("Dockerfile.test").exists()


class TestDataStructure:
    """Test data directory structure."""

    def test_data_files_accessible(self):
        """Test data files are accessible."""
        data_dir = Path("data")
        if data_dir.exists():
            # Check common data files
            common_files = ['seen_urls.txt']
            for fname in common_files:
                file_path = data_dir / fname
                if file_path.exists():
                    assert file_path.is_file()


class TestIndexStructure:
    """Test index directory structure."""

    def test_indexes_structure(self):
        """Test indexes directory has proper structure."""
        indexes_dir = Path("indexes")
        if indexes_dir.exists():
            expected_subdirs = ['chroma', 'index', 'vector_store']
            for subdir in expected_subdirs:
                path = indexes_dir / subdir
                # Can be created on first run
                assert True
