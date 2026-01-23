"""Shared pytest fixtures for all tests."""
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Test data directory."""
    return project_root / "tests" / "fixtures" / "sample_documents"

@pytest.fixture
def sample_text_file(test_data_dir, tmp_path):
    """Create a sample text file for testing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is a test document for RAG ingestion.")
    return test_file

@pytest.fixture
def mock_weaviate_url():
    """Mock Weaviate URL for testing."""
    return "http://weaviate:8080"

@pytest.fixture
def mock_ollama_url():
    """Mock Ollama URL for testing."""
    return "http://ollama:11434"