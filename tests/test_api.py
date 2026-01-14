from __future__ import annotations

from fastapi.testclient import TestClient

from src.app.dependencies import get_rag_service
from src.app.server import app


class FakeResult:
    def __init__(self, final_output: str, timings: dict[str, float]):
        self.final_output = final_output
        self.timings = timings


class FakeRAGService:
    def run_with_agents(self, topic: str, language: str = "en") -> FakeResult:
        return FakeResult(
            final_output="final-output",
            timings={
                "writer": 0.01,
                "reviewer": 0.01,
                "factchecker": 0.01,
                "translator": 0.0,
            },
        )


def test_health() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_rag_query_contract() -> None:
    # Override the dependency so we don't need Ollama/Haystack running
    app.dependency_overrides[get_rag_service] = lambda: FakeRAGService()
    try:
        client = TestClient(app)
        payload = {"query": "Explainable AI", "language": "de"}

        resp = client.post("/rag/query", json=payload)
        assert resp.status_code == 200

        data = resp.json()
        assert data["query"] == "Explainable AI"
        assert data["language"] == "de"
        assert data["answer"] == "final-output"
        assert set(data["timings"].keys()) == {
            "writer",
            "reviewer",
            "factchecker",
            "translator",
        }
    finally:
        app.dependency_overrides.clear()
