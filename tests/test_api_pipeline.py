from __future__ import annotations

from typing import Dict

from fastapi.testclient import TestClient

from src.agents.orchestrator import PipelineResult
from src.app import api as api_module
from src.app.server import app


def test_pipeline_summary_endpoint(monkeypatch) -> None:
    """
    Smoke test for /api/pipeline/summary.

    We patch RAG.run_with_agents so the test does not depend on Ollama or
    Haystack. This keeps CI fast and deterministic.
    """

    def fake_run_with_agents(topic: str, language: str = "en") -> PipelineResult:
        timings: Dict[str, float] = {
            "writer": 0.01,
            "reviewer": 0.01,
            "factchecker": 0.01,
            "translator": 0.0,
        }
        return PipelineResult(
            topic=topic,
            language=language,
            writer_output="writer-output",
            reviewed_output="reviewed-output",
            checked_output="checked-output",
            final_output="final-output",
            timings=timings,
        )

    # Patch the global RAG instance used inside api.py
    monkeypatch.setattr(api_module.RAG, "run_with_agents",
                        fake_run_with_agents)

    client = TestClient(app)

    payload = {
        "topic": "Explainable AI",
        "language": "de",
        "context": "ignored for now",
    }
    resp = client.post("/api/pipeline/summary", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["topic"] == "Explainable AI"
    assert data["language"] == "de"
    assert data["final_output"] == "final-output"
    assert "timings" in data
    assert set(data["timings"].keys()) == {
        "writer",
        "reviewer",
        "factchecker",
        "translator",
    }
