from __future__ import annotations

from dataclasses import dataclass

from src.agents.base import AgentConfig, BaseAgent
from src.agents.orchestrator import Orchestrator


@dataclass
class DummyAgent(BaseAgent):  # type: ignore[misc]
    label: str = "dummy"

    def __init__(self, label: str) -> None:  # type: ignore[override]
        cfg = AgentConfig(name=label, model="dummy-model")
        super().__init__(cfg)
        self.label = label

    def run(self, **kwargs) -> str:  # type: ignore[override]
        # Encode which agent we are + which keys we saw
        keys = ",".join(sorted(kwargs.keys()))
        return f"{self.label}:{keys}"


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

    result = orch.run_pipeline(topic="XAI", language="de", context="ctx")

    # Check that flow passed the expected keyword arguments
    assert result.writer_output.startswith("writer:")
    assert "topic" in result.writer_output
    assert "context" in result.writer_output

    assert result.reviewed_output.startswith("reviewer:")
    assert "draft" in result.reviewed_output

    assert result.checked_output.startswith("factchecker:")
    assert "text" in result.checked_output
    assert "context" in result.checked_output

    # For non-English language, translator should be used
    assert result.final_output.startswith("translator:")
    assert "text" in result.final_output
    assert "target_language" in result.final_output
