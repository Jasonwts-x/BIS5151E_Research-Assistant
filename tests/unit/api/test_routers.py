"""Unit tests for API routers."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.server import app


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


class TestSystemRouter:
    """Tests for system endpoints."""

    def test_health(self, client):
        """Test health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_version(self, client):
        """Test version endpoint returns service info."""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "api_version" in data
        assert data["service"] == "research-assistant-api"

    def test_ready_structure(self, client):
        """Test ready endpoint has correct structure."""
        with patch("src.api.routers.system._check_weaviate", return_value=True):
            with patch("src.api.routers.system._check_ollama_optional", return_value=True):
                response = client.get("/ready")
                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert "weaviate_ok" in data
                assert "ollama_ok" in data


class TestOllamaRouter:
    """Tests for Ollama endpoints."""

    def test_ollama_info(self, client):
        """Test Ollama info endpoint."""
        with patch("src.api.routers.ollama.ollama_list") as mock_list:
            mock_list.return_value = {
                "models": [
                    {"name": "qwen2.5:3b", "size": 1000000}
                ]
            }
            
            response = client.get("/ollama/info")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "configured_model" in data
            assert "available_models" in data

    def test_list_models(self, client):
        """Test list models endpoint."""
        with patch("src.api.routers.ollama.ollama_list") as mock_list:
            mock_list.return_value = {
                "models": [
                    {
                        "name": "qwen2.5:3b",
                        "size": 1000000,
                        "digest": "abc123",
                        "modified_at": "2024-01-01T00:00:00"
                    }
                ]
            }
            
            response = client.get("/ollama/models")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert len(data["models"]) == 1
            assert data["models"][0]["name"] == "qwen2.5:3b"


class TestCrewAIRouter:
    """Tests for CrewAI proxy endpoints."""

    @pytest.mark.asyncio
    async def test_crewai_run_proxy(self, client):
        """Test CrewAI run endpoint proxies correctly."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "topic": "test",
            "language": "en",
            "answer": "Test answer"
        }
        mock_response.raise_for_status = AsyncMock()
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch("src.api.routers.crewai.httpx.AsyncClient", return_value=mock_client):
            response = client.post(
                "/crewai/run",
                json={"topic": "test", "language": "en"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["topic"] == "test"
            assert data["answer"] == "Test answer"

    def test_crewai_status_not_implemented(self, client):
        """Test status endpoint returns 501."""
        response = client.get("/crewai/status/test-job-id")
        assert response.status_code == 501


class TestRAGRouter:
    """Tests for RAG endpoints."""

    @pytest.mark.asyncio
    async def test_rag_query_proxies_to_crew(self, client):
        """Test RAG query proxies to CrewAI service."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "topic": "AI",
            "language": "en",
            "answer": "AI is..."
        }
        mock_response.raise_for_status = AsyncMock()
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        with patch("src.api.routers.rag.httpx.AsyncClient", return_value=mock_client):
            response = client.post(
                "/rag/query",
                json={"query": "What is AI?", "language": "en"}
            )
            
            assert response.status_code == 200
            assert "answer" in response.json()

    def test_ingest_local_endpoint(self, client):
        """Test local ingestion endpoint."""
        mock_result = MagicMock()
        mock_result.source_name = "LocalFiles"
        mock_result.documents_loaded = 1
        mock_result.chunks_created = 5
        mock_result.chunks_ingested = 5
        mock_result.chunks_skipped = 0
        mock_result.errors = []
        
        with patch("src.api.routers.rag.IngestionEngine") as mock_engine:
            mock_instance = mock_engine.return_value
            mock_instance.ingest_from_source.return_value = mock_result
            
            response = client.post(
                "/rag/ingest/local",
                json={"pattern": "*"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["chunks_ingested"] == 5

    def test_get_stats(self, client):
        """Test stats endpoint."""
        with patch("src.api.routers.rag.IngestionEngine") as mock_engine:
            mock_instance = mock_engine.return_value
            mock_instance.get_stats.return_value = {
                "collection_name": "ResearchDocument",
                "schema_version": "1.0.0",
                "document_count": 10,
                "exists": True
            }
            
            response = client.get("/rag/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["document_count"] == 10