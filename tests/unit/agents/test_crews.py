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

    def test_run_creates_correct_agents_for_english(self, crew):
        """Test English workflow uses 3 agents."""
        with patch("src.agents.crews.research_crew.Crew") as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = "Final output"
            mock_crew_class.return_value = mock_crew_instance
            
            crew.run(topic="test", context="context", language="en")
            
            # Should be called with 3 agents (no translator)
            call_args = mock_crew_class.call_args
            agents = call_args.kwargs["agents"]
            assert len(agents) == 3

    def test_run_creates_correct_agents_for_german(self, crew):
        """Test German workflow uses 4 agents."""
        with patch("src.agents.crews.research_crew.Crew") as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = "Final output"
            mock_crew_class.return_value = mock_crew_instance
            
            crew.run(topic="test", context="context", language="de")
            
            # Should be called with 4 agents (includes translator)
            call_args = mock_crew_class.call_args
            agents = call_args.kwargs["agents"]
            assert len(agents) == 4

    def test_run_returns_string(self, crew):
        """Test run returns string output."""
        with patch("src.agents.crews.research_crew.Crew") as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = "Test output"
            mock_crew_class.return_value = mock_crew_instance
            
            result = crew.run(topic="test", context="context", language="en")
            
            assert isinstance(result, str)
            assert result == "Test output"