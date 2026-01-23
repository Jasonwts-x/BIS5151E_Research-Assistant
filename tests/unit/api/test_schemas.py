"""Unit tests for API schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.api.schemas.crewai import CrewRunRequest, CrewRunResponse
from src.api.schemas.rag import (
    IngestArxivRequest,
    IngestLocalRequest,
    RAGQueryRequest,
)


class TestCrewAISchemas:
    """Tests for CrewAI schemas."""

    def test_crew_run_request_valid(self):
        """Test valid CrewRunRequest."""
        request = CrewRunRequest(
            topic="What is AI?",
            language="en"
        )
        assert request.topic == "What is AI?"
        assert request.language == "en"

    def test_crew_run_request_defaults(self):
        """Test CrewRunRequest defaults."""
        request = CrewRunRequest(topic="test")
        assert request.language == "en"

    def test_crew_run_request_empty_topic_fails(self):
        """Test empty topic fails validation."""
        with pytest.raises(ValidationError):
            CrewRunRequest(topic="", language="en")

    def test_crew_run_response_valid(self):
        """Test valid CrewRunResponse."""
        response = CrewRunResponse(
            topic="test",
            language="en",
            answer="Test answer"
        )
        assert response.topic == "test"
        assert response.answer == "Test answer"


class TestRAGSchemas:
    """Tests for RAG schemas."""

    def test_rag_query_request_valid(self):
        """Test valid RAGQueryRequest."""
        request = RAGQueryRequest(
            query="What is AI?",
            language="en"
        )
        assert request.query == "What is AI?"
        assert request.language == "en"

    def test_rag_query_request_defaults(self):
        """Test RAGQueryRequest defaults."""
        request = RAGQueryRequest(query="test")
        assert request.language == "en"

    def test_ingest_local_request_defaults(self):
        """Test IngestLocalRequest defaults."""
        request = IngestLocalRequest()
        assert request.pattern == "*"

    def test_ingest_local_request_custom_pattern(self):
        """Test IngestLocalRequest with custom pattern."""
        request = IngestLocalRequest(pattern="arxiv*")
        assert request.pattern == "arxiv*"

    def test_ingest_arxiv_request_valid(self):
        """Test valid IngestArxivRequest."""
        request = IngestArxivRequest(
            query="machine learning",
            max_results=5
        )
        assert request.query == "machine learning"
        assert request.max_results == 5

    def test_ingest_arxiv_request_defaults(self):
        """Test IngestArxivRequest defaults."""
        request = IngestArxivRequest(query="test")
        assert request.max_results == 5

    def test_ingest_arxiv_request_max_results_bounds(self):
        """Test max_results bounds validation."""
        # Should fail if < 1
        with pytest.raises(ValidationError):
            IngestArxivRequest(query="test", max_results=0)
        
        # Should fail if > 20
        with pytest.raises(ValidationError):
            IngestArxivRequest(query="test", max_results=21)
        
        # Should succeed at boundaries
        request1 = IngestArxivRequest(query="test", max_results=1)
        assert request1.max_results == 1
        
        request20 = IngestArxivRequest(query="test", max_results=20)
        assert request20.max_results == 20