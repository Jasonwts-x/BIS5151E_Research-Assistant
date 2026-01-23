"""Integration test for RAG query endpoint with Ollama."""
from __future__ import annotations

import os

import pytest
import requests


@pytest.fixture
def api_base_url() -> str:
    """Get API base URL from environment or use default."""
    return os.getenv("API_URL", "http://localhost:8000")


def test_api_health(api_base_url: str) -> None:
    """Test API health endpoint."""
    response = requests.get(f"{api_base_url}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_ready_ollama_check(api_base_url: str) -> None:
    """Test readiness endpoint includes Ollama check."""
    response = requests.get(f"{api_base_url}/ready", timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    assert "weaviate_ok" in data
    assert "ollama_ok" in data
    
    # Ollama should be reachable (True) or not configured (None)
    # Should not be False (unreachable)
    assert data["ollama_ok"] in [True, None], "Ollama is configured but unreachable"


@pytest.mark.slow
def test_rag_query_with_ollama(api_base_url: str) -> None:
    """Test full RAG query endpoint (slow - calls LLM)."""
    payload = {
        "query": "What is digital transformation?",
        "language": "en"
    }
    
    response = requests.post(
        f"{api_base_url}/rag/query",
        json=payload,
        timeout=60  # LLM calls can be slow
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["language"] == payload["language"]
    assert len(data["answer"]) > 0, "Answer should not be empty"
    
    # Check that we got timing information
    assert "timings" in data
    assert "writer" in data["timings"]
    
    print(f"\n📝 Answer preview: {data['answer'][:200]}...")