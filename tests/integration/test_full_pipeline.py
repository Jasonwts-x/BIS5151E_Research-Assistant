"""End-to-end integration test for full pipeline."""
from __future__ import annotations

import os

import pytest
import requests


@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS", "").lower() in {"1", "true"},
    reason="Integration tests skipped"
)
class TestFullPipeline:
    """Test complete workflow from ingestion to query."""

    @pytest.fixture(scope="class")
    def api_url(self):
        """API URL."""
        return os.getenv("API_URL", "http://localhost:8000")

    @pytest.fixture(scope="class")
    def setup_test_data(self, api_url, tmp_path_factory):
        """Ingest test data before running tests."""
        # Create test file
        data_dir = tmp_path_factory.mktemp("test_data")
        test_file = data_dir / "test_document.txt"
        test_file.write_text(
            "Machine learning is a method of data analysis that automates analytical model building. "
            "It is a branch of artificial intelligence based on the idea that systems can learn from data, "
            "identify patterns and make decisions with minimal human intervention."
        )
        
        # Reset index
        requests.delete(f"{api_url}/rag/admin/reset-index", timeout=30)
        
        # Ingest test file (would need to copy to container)
        # For now, use existing data
        yield
        
        # Cleanup (optional)
        pass

    def test_complete_workflow(self, api_url, setup_test_data):
        """Test: Ingest → Query → Verify."""
        # Step 1: Check health
        response = requests.get(f"{api_url}/health", timeout=5)
        assert response.status_code == 200
        
        # Step 2: Ingest local data
        response = requests.post(
            f"{api_url}/rag/ingest/local",
            json={"pattern": "*"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_ingested"] > 0, "No documents ingested!"
        
        # Step 3: Query
        response = requests.post(
            f"{api_url}/rag/query",
            json={
                "query": "What is machine learning?",
                "language": "en"
            },
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        # Step 4: Verify answer
        answer = data["answer"]
        assert len(answer) > 100, "Answer too short"
        assert "machine learning" in answer.lower(), "Answer doesn't mention ML"
        
        # Step 5: Check stats
        response = requests.get(f"{api_url}/rag/stats", timeout=5)
        assert response.status_code == 200
        stats = response.json()
        assert stats["document_count"] > 0