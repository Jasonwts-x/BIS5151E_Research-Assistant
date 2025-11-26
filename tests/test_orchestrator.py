from __future__ import annotations

from typing import Any

from src.agents.base import AgentConfig, BaseAgent
from src.agents.orchestrator import Orchestrator, PipelineResult


class DummyAgent(BaseAgent):
    """
    Simple dummy agent that records how it was called and returns a tagged string.
    We use it to test the Orchestrator without hitting the real LLM.
    """

    def __init__(self, label: str) -> None:  # type: ignore[override]
        cfg = AgentConfig(
            name=label,
            role=label,  # new field required by AgentConfig
            model="dummy-model",
            system_prompt="",
            temperature=0.0,
        )
        super().__init__(cfg)

    def run(self, **kwargs: Any) -> str:  # type: ignore[override]
        # We just encode the kwargs into the output so the test can inspect them.
        return f"{self.config.name}-called-with:{sorted(kwargs.keys())}"


def test_pipeline_flow() -> None:
    writer = DummyAgent("writer")
    reviewer = DummyAgent("reviewer")
    factchecker = DummyAgent("factchecker")
    translator = DummyAgent("translator")

    orch = Orchestrator(
        writer=writer,
        reviewer=reviewer,
        factchecker=factchecker,
        translator=translator,
    )

    result = orch.run_pipeline(
        topic="test-topic",
        language="de",
        context="some context",
    )

    assert isinstance(result, PipelineResult)
    assert result.topic == "test-topic"
    assert result.language == "de"

    # Check that each step produced some output from the dummy agents.
    assert "writer-called-with" in result.writer_output
    assert "reviewer-called-with" in result.reviewed_output
    assert "factchecker-called-with" in result.checked_output
    # Because language != "en" and translator is provided, translator must be used:
    assert "translator-called-with" in result.final_output
