"""Integration tests for complete evaluation workflow."""
from __future__ import annotations

import pytest


@pytest.mark.integration
class TestEvaluationWorkflow:
    """Test complete evaluation workflow end-to-end."""

    def test_full_evaluation_workflow(self):
        """Test complete workflow from query to evaluation storage."""
        from src.agents.runner import CrewRunner

        # Create runner with evaluation enabled
        runner = CrewRunner(
            enable_guardrails=True,
            enable_monitoring=True,
        )

        # Run query
        result = runner.run(
            topic="What is retrieval augmented generation?",
            language="en",
        )

        # Check result has evaluation
        assert result.evaluation is not None

        # Check evaluation structure
        assert "performance" in result.evaluation
        assert "trulens" in result.evaluation
        assert "guardrails" in result.evaluation

        # Check performance metrics
        perf = result.evaluation["performance"]
        assert "total_time" in perf
        assert perf["total_time"] > 0

        # Check TruLens metrics
        trulens = result.evaluation["trulens"]
        assert "overall_score" in trulens
        assert "record_id" in trulens

        # Check guardrails
        guards = result.evaluation["guardrails"]
        assert "input_passed" in guards
        assert "output_passed" in guards

    def test_evaluation_stored_in_database(self):
        """Test evaluation results are stored in database."""
        from src.agents.runner import CrewRunner
        from src.eval.database import get_database
        from src.eval.models import EvaluationRecord

        runner = CrewRunner(
            enable_guardrails=True,
            enable_monitoring=True,
        )

        # Run query
        result = runner.run(
            topic="What is machine learning?",
            language="en",
        )

        # Get record_id from evaluation
        record_id = result.evaluation["trulens"]["record_id"]

        # Check record exists in database
        db = get_database()
        with db.get_session() as session:
            record = (
                session.query(EvaluationRecord)
                .filter_by(record_id=record_id)
                .first()
            )

            assert record is not None
            assert record.input == "What is machine learning?"

    def test_leaderboard_after_evaluation(self):
        """Test leaderboard shows evaluation after query."""
        from src.agents.runner import CrewRunner
        from src.eval.trulens import TruLensClient

        runner = CrewRunner(
            enable_guardrails=True,
            enable_monitoring=True,
        )

        # Run query
        result = runner.run(
            topic="What is deep learning?",
            language="en",
        )

        # Get leaderboard
        client = TruLensClient(enabled=True)
        leaderboard = client.get_leaderboard(limit=10)

        # Should have at least one entry
        assert len(leaderboard) > 0

        # Find our record
        record_id = result.evaluation["trulens"]["record_id"]
        found = any(entry["record_id"] == record_id for entry in leaderboard)
        assert found

    @pytest.mark.asyncio
    async def test_async_evaluation_workflow(self):
        """Test async evaluation workflow."""
        from src.eval.trulens import TruLensClient

        client = TruLensClient(enabled=True)

        # Async evaluation
        result = await client.evaluate_async(
            query="What is AI?",
            context="AI is artificial intelligence.",
            answer="AI is a field of computer science.",
        )

        assert "record_id" in result

        # Verify stored in database
        record_id = result["record_id"]
        stored = client.get_record(record_id)

        assert stored is not None
        assert stored["record_id"] == record_id