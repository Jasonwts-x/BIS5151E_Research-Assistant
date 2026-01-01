import os

import pytest
import requests

import src.rag.pipeline as pipeline_module
from src.rag.pipeline import RAGPipeline
from src.utils.config import load_config


def _weaviate_reachable(url: str) -> bool:
    # Weaviate exposes /v1/meta on a running instance
    meta_url = f"{url.rstrip('/')}/v1/meta"
    try:
        r = requests.get(meta_url, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def test_rag_pipeline_builds_and_retrieves(tmp_path, monkeypatch) -> None:
    """
    Integration-ish smoke test:
    - skips if Weaviate isn't reachable
    - creates a tiny local doc
    - builds the pipeline and retrieves results
    """
    if os.getenv("SKIP_WEAVIATE_TESTS", "").lower() in {"1", "true", "yes"}:
        pytest.skip("Skipping Weaviate tests via SKIP_WEAVIATE_TESTS")

    cfg = load_config()
    if not _weaviate_reachable(cfg.weaviate.url):
        pytest.skip(f"Weaviate not reachable at {cfg.weaviate.url}")

    # Ensure we always have at least one document to index
    (tmp_path / "sample.txt").write_text(
        "Explainable AI (XAI) aims to make machine learning decisions understandable.",
        encoding="utf-8",
    )

    # Point the pipeline at our temp raw-data dir
    monkeypatch.setattr(pipeline_module, "DATA_DIR", tmp_path)

    pipeline = RAGPipeline.from_config()
    docs = pipeline.run("Explainable AI", top_k=3)

    assert isinstance(docs, list)
    assert len(docs) > 0
