from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.server import app


def test_health() -> None:
    """Test basic health endpoint."""
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_version() -> None:
    """Test version endpoint."""
    client = TestClient(app)
    resp = client.get("/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "service" in data
    assert "api_version" in data
    assert "python_version" in data


@pytest.mark.asyncio
async def test_rag_query_calls_crewai_service() -> None:
    """
    Test that /rag/query endpoint properly proxies to CrewAI service.
    
    This test mocks the HTTP call to the CrewAI service to avoid
    needing the actual service running during tests.
    """
    client = TestClient(app)
    
    # Mock the HTTP call to CrewAI service
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "topic": "test topic",
        "language": "en",
        "answer": "This is a test answer with citations [1].",
    }
    mock_response.raise_for_status = AsyncMock()
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    with patch("src.api.routers.rag.httpx.AsyncClient", return_value=mock_client):
        payload = {
            "query": "test topic",
            "language": "en",
        }
        
        resp = client.post("/rag/query", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "test topic"
        assert data["language"] == "en"
        assert "answer" in data
        assert len(data["answer"]) > 0
        
        # Verify the CrewAI service was called
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/crew/run" in call_args[0][0]


@pytest.mark.asyncio
async def test_crewai_proxy_endpoint() -> None:
    """
    Test the /crewai/run proxy endpoint.
    
    This endpoint directly proxies to the CrewAI service without
    additional processing.
    """
    client = TestClient(app)
    
    # Mock the HTTP call to CrewAI service
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "topic": "artificial intelligence",
        "language": "en",
        "answer": "AI is a field of computer science [1].",
    }
    mock_response.raise_for_status = AsyncMock()
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    with patch("src.api.routers.crewai.httpx.AsyncClient", return_value=mock_client):
        payload = {
            "topic": "artificial intelligence",
            "language": "en",
        }
        
        resp = client.post("/crewai/run", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["topic"] == "artificial intelligence"
        assert data["answer"].startswith("AI is")