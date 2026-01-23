"""
Integration tests for RAG ingestion endpoints.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.server import app


@pytest.fixture
def client():
    """Test client for API."""
    return TestClient(app)


def test_ingest_local_endpoint(client):
    """Test POST /rag/ingest/local endpoint."""
    # Mock the ingestion engine
    mock_result = MagicMock()
    mock_result.source_name = "LocalFiles"
    mock_result.documents_loaded = 2
    mock_result.chunks_created = 10
    mock_result.chunks_ingested = 10
    mock_result.chunks_skipped = 0
    mock_result.errors = []
    
    with patch("src.api.routers.rag.IngestionEngine") as mock_engine:
        mock_instance = mock_engine.return_value
        mock_instance.ingest_from_source.return_value = mock_result
        
        response = client.post(
            "/rag/ingest/local",
            json={"pattern": "*"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["source"] == "LocalFiles"
        assert data["documents_loaded"] == 2
        assert data["chunks_ingested"] == 10
        assert data["success"] is True


def test_ingest_arxiv_endpoint(client):
    """Test POST /rag/ingest/arxiv endpoint."""
    mock_result = MagicMock()
    mock_result.source_name = "ArXiv"
    mock_result.documents_loaded = 3
    mock_result.chunks_created = 25
    mock_result.chunks_ingested = 25
    mock_result.chunks_skipped = 0
    mock_result.errors = []
    
    with patch("src.api.routers.rag.IngestionEngine") as mock_engine:
        mock_instance = mock_engine.return_value
        mock_instance.ingest_from_source.return_value = mock_result
        
        response = client.post(
            "/rag/ingest/arxiv",
            json={
                "query": "machine learning",
                "max_results": 3,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["source"] == "ArXiv"
        assert data["documents_loaded"] == 3
        assert data["chunks_ingested"] == 25
        assert data["success"] is True


def test_get_stats_endpoint(client):
    """Test GET /rag/stats endpoint."""
    with patch("src.api.routers.rag.IngestionEngine") as mock_engine:
        mock_instance = mock_engine.return_value
        mock_instance.get_stats.return_value = {
            "collection_name": "ResearchDocument",
            "schema_version": "1.0.0",
            "document_count": 42,
            "exists": True,
        }
        
        response = client.get("/rag/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["collection_name"] == "ResearchDocument"
        assert data["document_count"] == 42
        assert data["exists"] is True


def test_reset_index_endpoint(client):
    """Test DELETE /rag/admin/reset-index endpoint."""
    with patch("src.api.routers.rag.IngestionEngine") as mock_engine:
        mock_instance = mock_engine.return_value
        mock_instance.get_stats.return_value = {
            "document_count": 42,
        }
        mock_instance.clear_index.return_value = None
        
        response = client.delete("/rag/admin/reset-index")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["previous_document_count"] == 42
        assert "cleared successfully" in data["message"].lower()