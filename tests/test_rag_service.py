import os
import re
from typing import Tuple

import pytest
import requests

import src.rag.pipeline as pipeline_module
from src.rag.pipeline import RAGPipeline
from src.utils.config import load_config


def _parse_version(v: str) -> Tuple[int, int, int]:
    """
    Parse versions like '1.27.0', '1.25.7', or '1.27.0-rc.1' into (major, minor, patch).
    Unknown formats return (0, 0, 0).
    """
    m = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)", v or "")
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _weaviate_reachable_and_supported(url: str) -> bool:
    """
    Returns True only if:
    - Weaviate is reachable at /v1/meta
    - version >= 1.27.0 (required by weaviate client used via weaviate-haystack)
    """
    meta_url = f"{url.rstrip('/')}/v1/meta"
    try:
        r = requests.get(meta_url, timeout=2)
        if r.status_code != 200:
            return False
        data = r.json()
        version = _parse_version(str(data.get("version", "")))
        return version >= (1, 27, 0)
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
    if not _weaviate_reachable_and_supported(cfg.weaviate.url):
        pytest.skip(f"Weaviate not reachable or unsupported at {cfg.weaviate.url}")

    # Ensure we always have at least one document to index
    (tmp_path / "sample.txt").write_text(
        "Explainable AI (XAI) aims to make machine learning decisions understandable.",
        encoding="utf-8",
    )

    # Point the pipeline at our temp raw-data dir
    monkeypatch.setattr(pipeline_module, "DATA_DIR", tmp_path)

    pipeline = RAGPipeline.from_config()
    try:
        docs = pipeline.run("Explainable AI", top_k=3)
    finally:
        # Best effort cleanup (avoid ResourceWarning if possible)
        store = getattr(pipeline, "store", None)
        client = getattr(store, "client", None) if store is not None else None
        close = getattr(client, "close", None)
        if callable(close):
            close()

    assert isinstance(docs, list)
    assert len(docs) > 0
