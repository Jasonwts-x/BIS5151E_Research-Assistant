"""Unit tests for ResearchCrew."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.agents.crews.research_crew import ResearchCrew


class TestResearchCrew:
    """Tests for ResearchCrew."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM."""
        return MagicMock()

    @pytest.fixture
    def crew(self, mock_llm):
        """Create crew with mocked agents."""
        with patch("src.agents.crews.research_crew.create_writer_agent"):
            with patch("src.agents.crews.research_crew.create_reviewer_agent"):
                with patch("src.agents.crews.research_crew.create_factchecker_agent"):
                    with patch("src.agents.crews.research_crew.create_translator_agent"):
                        return ResearchCrew(mock_llm)

    def test_crew_initialization(self, crew):
        """Test crew initializes with all agents."""
        assert crew.writer is not None
        assert crew.reviewer is not None
        assert crew.factchecker is not None
        assert crew.translator is not None

    def test_has_valid_context_with_valid_context(self, crew):
        """Test validation accepts context with SOURCE markers."""
        # Simulate actual formatted context
        context = """
╔═══════════════════════════════════════════════════════════════╗
║   AVAILABLE SOURCES - USE ONLY THESE IN YOUR RESPONSE        ║
╚═══════════════════════════════════════════════════════════════╝

  [1] test-paper.pdf

⚠️ CRITICAL: You may ONLY cite sources listed above.

═══════════════════════════════════════════
SOURCE [1]: test-paper.pdf
═══════════════════════════════════════════
This is test content about neural networks.
"""
        assert crew._has_valid_context(context) is True

    def test_has_valid_context_rejects_no_context(self, crew):
        """Test validation rejects empty context message."""
        context = "⚠️ NO CONTEXT AVAILABLE ⚠️\nNo documents were retrieved."
        assert crew._has_valid_context(context) is False

    def test_has_valid_context_rejects_short_context(self, crew):
        """Test validation rejects context that's too short."""
        context = "Short message"
        assert crew._has_valid_context(context) is False

    def test_has_valid_context_rejects_no_source_markers(self, crew):
        """Test validation rejects context without SOURCE markers."""
        context = "This is a long message but it has no source markers at all. " * 10
        assert crew._has_valid_context(context) is False

    def test_run_uses_strict_mode_with_valid_context(self, crew):
        """Test that valid context triggers strict mode."""
        valid_context = """
SOURCE [1]: test.pdf
This is valid context with enough text.
""" * 5  # Make it long enough
        
        with patch.object(crew, '_run_strict_mode', return_value="strict output") as mock_strict:
            with patch.object(crew, '_run_fallback_mode') as mock_fallback:
                result = crew.run(topic="test", context=valid_context, language="en")
                
                mock_strict.assert_called_once()
                mock_fallback.assert_not_called()
                assert result == "strict output"

    def test_run_uses_fallback_mode_with_no_context(self, crew):
        """Test that no context triggers fallback mode."""
        no_context = "⚠️ NO CONTEXT AVAILABLE ⚠️\nNo documents were retrieved."
        
        with patch.object(crew, '_run_strict_mode') as mock_strict:
            with patch.object(crew, '_run_fallback_mode', return_value="fallback output") as mock_fallback:
                result = crew.run(topic="test", context=no_context, language="en")
                
                mock_strict.assert_not_called()
                mock_fallback.assert_called_once()
                assert result == "fallback output"

    def test_run_creates_correct_agents_for_english(self, crew):
        """Test English workflow uses 3 agents."""
        valid_context = "SOURCE [1]: test\n" + ("Content " * 50)
        
        with patch("src.agents.crews.research_crew.Crew") as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = "Final output"
            mock_crew_class.return_value = mock_crew_instance
            
            crew.run(topic="test", context=valid_context, language="en")
            
            # Should be called with 3 agents (no translator)
            call_args = mock_crew_class.call_args
            agents = call_args.kwargs["agents"]
            assert len(agents) == 3

    def test_run_returns_string(self, crew):
        """Test run returns string output."""
        valid_context = "SOURCE [1]: test\n" + ("Content " * 50)
        
        with patch("src.agents.crews.research_crew.Crew") as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = "Test output"
            mock_crew_class.return_value = mock_crew_instance
            
            result = crew.run(topic="test", context=valid_context, language="en")
            
            assert isinstance(result, str)
            assert result == "Test output"