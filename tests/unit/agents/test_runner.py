"""Unit tests for CrewRunner."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from haystack.dataclasses import Document

from src.agents.runner import CrewRunner


class TestCrewRunner:
    """Tests for CrewRunner."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = MagicMock()
        config.llm.model = "qwen2.5:3b"
        config.llm.host = "http://ollama:11434"
        config.rag.top_k = 5
        return config

    @pytest.fixture
    def runner(self, mock_config):
        """Create runner with mocked dependencies."""
        with patch("src.agents.runner.load_config", return_value=mock_config):
            with patch("src.agents.runner.LLM"):
                # 🔧 CHANGED: Mock new evaluation modules
                with patch("src.agents.runner.load_guardrails_config"):
                    with patch("src.agents.runner.InputValidator"):
                        with patch("src.agents.runner.OutputValidator"):
                            with patch("src.agents.runner.TruLensClient"):
                                runner = CrewRunner(
                                    enable_guardrails=False,
                                    enable_monitoring=False
                                )
                                runner.rag_pipeline = None  # Disable RAG for unit tests
                                return runner

    def test_format_context_empty(self, runner):
        """Test formatting empty document list."""
        context = runner._format_context([])
        assert "NO CONTEXT AVAILABLE" in context

    def test_format_context_with_docs(self, runner):
        """Test formatting documents with citations."""
        docs = [
            Document(
                content="AI is a field of computer science.",
                meta={"source": "test1.txt"}
            ),
            Document(
                content="Machine learning is a subset of AI.",
                meta={"source": "test2.txt"}
            )
        ]
        
        context = runner._format_context(docs)
        
        # Should have source markers
        assert "SOURCE [1]" in context
        assert "SOURCE [2]" in context
        assert "test1.txt" in context
        assert "test2.txt" in context
        
        # Should have content
        assert "AI is a field" in context
        assert "Machine learning" in context

    def test_format_context_deduplicates_sources(self, runner):
        """Test that multiple chunks from same source use same citation."""
        docs = [
            Document(content="First chunk", meta={"source": "paper.txt"}),
            Document(content="Second chunk", meta={"source": "paper.txt"}),
        ]
        
        context = runner._format_context(docs)
        
        # Both should use [1]
        assert context.count("SOURCE [1]") == 2
        assert "SOURCE [2]" not in context

    def test_retrieve_context_no_pipeline(self, runner):
        """Test retrieve_context when RAG pipeline is None."""
        runner.rag_pipeline = None
        
        context, docs = runner.retrieve_context("test topic")
        
        assert "No context available" in context or "not initialized" in context
        assert docs == []

    def test_crew_result_includes_evaluation(self):
        """Test that CrewResult includes evaluation field."""
        from src.agents.runner import CrewResult
        
        evaluation = {
            "trulens": {"overall_score": 0.85},
            "guardrails": {"input_passed": True, "output_passed": True},
            "performance": {"total_time": 45.2}
        }
        
        result = CrewResult(
            topic="test",
            language="en",
            final_output="Test output",
            context_docs=[],
            evaluation=evaluation
        )
        
        assert result.evaluation is not None
        assert result.evaluation["trulens"]["overall_score"] == 0.85
        assert result.evaluation["guardrails"]["input_passed"] is True
        assert result.evaluation["performance"]["total_time"] == 45.2

    def test_crew_result_evaluation_optional(self):
        """Test that evaluation field is optional."""
        from src.agents.runner import CrewResult
        
        result = CrewResult(
            topic="test",
            language="en",
            final_output="Test output",
            context_docs=[]
        )
        
        assert result.evaluation is None


class TestCrewResult:
    """Tests for CrewResult dataclass."""

    def test_crew_result_creation(self):
        """Test creating CrewResult."""
        from src.agents.runner import CrewResult
        
        result = CrewResult(
            topic="test",
            language="en",
            final_output="Test output",
            context_docs=[]
        )
        
        assert result.topic == "test"
        assert result.language == "en"
        assert result.final_output == "Test output"
        assert result.context_docs == []
        assert result.evaluation is None