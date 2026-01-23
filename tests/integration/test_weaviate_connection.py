"""Integration tests for Weaviate connection."""
from __future__ import annotations

import os

import pytest
import requests


@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS", "").lower() in {"1", "true"},
    reason="Integration tests skipped"
)
class TestWeaviateConnection:
    """Tests for Weaviate connectivity."""

    @pytest.fixture(scope="class")
    def weaviate_url(self):
        """Weaviate URL."""
        return os.getenv("WEAVIATE_URL", "http://localhost:8080")

    def test_weaviate_reachable(self, weaviate_url):
        """Test Weaviate is reachable."""
        response = requests.get(f"{weaviate_url}/v1/.well-known/ready", timeout=5)
        assert response.status_code == 200

    def test_weaviate_meta(self, weaviate_url):
        """Test Weaviate returns version info."""
        response = requests.get(f"{weaviate_url}/v1/meta", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data

    def test_weaviate_schema_endpoint(self, weaviate_url):
        """Test Weaviate schema endpoint works."""
        response = requests.get(f"{weaviate_url}/v1/schema", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert "classes" in data

    def test_create_weaviate_client_from_config(self):
        """Test creating Weaviate client from config."""
        from src.utils.config import load_config
        from src.rag.ingestion.engine import IngestionEngine
        
        config = load_config()
        engine = IngestionEngine()
        
        try:
            # Client should be created successfully
            assert engine.client is not None
            
            # Should be able to list collections
            collections = engine.client.collections.list_all()
            assert isinstance(collections, dict)
        finally:
            engine.client.close()