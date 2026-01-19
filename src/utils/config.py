from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "configs" / "app.yaml"


# ----------------------------------------------------------------------
# Dataclasses
# ----------------------------------------------------------------------


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "llama3"
    host: str = "http://localhost:11434"


@dataclass
class RAGConfig:
    backend: str = "weaviate"  # in-memory, weaviate, etc.
    chunk_size: int = 350
    chunk_overlap: int = 60
    top_k: int = 5


@dataclass
class WeaviateConfig:
    url: str = "http://localhost:8080"
    api_key: Optional[str] = None
    index_name: str = "research_assistant"
    text_key: str = "content"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class GuardrailsConfig:
    citation_required: bool = True


@dataclass
class EvalConfig:
    faithfulness_metric: str = "trulens_groundedness"


@dataclass
class AppConfig:
    llm: LLMConfig
    rag: RAGConfig
    weaviate: WeaviateConfig
    guardrails: GuardrailsConfig
    eval: EvalConfig


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config() -> AppConfig:
    """
    Load configuration from configs/app.yaml and .env (env overrides YAML).
    """
    # Load .env first so os.getenv can see values
    load_dotenv(ROOT / ".env", override=False)

    y = _read_yaml(CONFIG_FILE)
    if not y:
        print(
            f"ℹ️  No configs/app.yaml found at {CONFIG_FILE}, using defaults/env only."
        )

    llm_y = y.get("llm") or {}
    rag_y = y.get("rag") or {}
    weav_y = rag_y.get("weaviate") or {}
    guard_y = y.get("guardrails") or {}
    eval_y = y.get("eval") or {}

    # ---------------- LLM ----------------
    # Read model name WITHOUT provider prefix
    # Provider prefix will be added by CrewRunner when needed
    llm_model = os.getenv("LLM_MODEL", llm_y.get("model", "qwen2.5:3b"))
    # Remove "ollama/" prefix if present in env var
    if llm_model.startswith("ollama/"):
        llm_model = llm_model.replace("ollama/", "")

    llm_host = os.getenv("OLLAMA_HOST", llm_y.get(
        "host", "http://ollama:11434"))

    llm = LLMConfig(
        provider=llm_y.get("provider", "ollama"),
        model=llm_model,  # Just the model name, e.g. "qwen3:4b"
        host=llm_host,
    )

    # ---------------- RAG ----------------
    rag_backend = os.getenv("RAG_BACKEND", rag_y.get("backend", "weaviate"))
    rag_chunk_size = int(
        os.getenv("RAG_CHUNK_SIZE", rag_y.get("chunk_size", 350)))
    rag_chunk_overlap = int(
        os.getenv("RAG_CHUNK_OVERLAP", rag_y.get("chunk_overlap", 60))
    )
    rag_top_k = int(os.getenv("RAG_TOP_K", rag_y.get("top_k", 5)))

    rag_chunk_size = max(1, rag_chunk_size)
    rag_chunk_overlap = max(0, rag_chunk_overlap)
    rag_top_k = max(1, rag_top_k)

    rag = RAGConfig(
        backend=rag_backend,
        chunk_size=rag_chunk_size,
        chunk_overlap=rag_chunk_overlap,
        top_k=rag_top_k,
    )

    # -------------- Weaviate -------------
    weav_url = os.getenv("WEAVIATE_URL", weav_y.get(
        "url", "http://localhost:8080"))

    weav_api_key_env = os.getenv("WEAVIATE_API_KEY", "")
    weav_api_key_yaml = weav_y.get("api_key") or ""
    weav_api_key = weav_api_key_env or weav_api_key_yaml or None

    weav_index_name = os.getenv(
        "WEAVIATE_INDEX_NAME", weav_y.get("index_name", "research_assistant")
    )
    weav_text_key = os.getenv(
        "WEAVIATE_TEXT_KEY", weav_y.get("text_key", "content"))

    weav_embedding_model = os.getenv(
        "WEAVIATE_EMBEDDING_MODEL",
        weav_y.get("embedding_model",
                   "sentence-transformers/all-MiniLM-L6-v2"),
    )

    weaviate = WeaviateConfig(
        url=weav_url,
        api_key=weav_api_key,
        index_name=weav_index_name,
        text_key=weav_text_key,
        embedding_model=weav_embedding_model,
    )

    # -------------- Guardrails -----------
    citation_required_env = os.getenv("GUARDRAILS_CITATION_REQUIRED")
    if citation_required_env is not None:
        citation_required = citation_required_env.lower() in {
            "1", "true", "yes"}
    else:
        citation_required = bool(guard_y.get("citation_required", True))

    guardrails = GuardrailsConfig(citation_required=citation_required)

    # -------------- Eval -----------------
    faithfulness_metric = os.getenv(
        "EVAL_FAITHFULNESS_METRIC",
        eval_y.get("faithfulness_metric", "trulens_groundedness"),
    )
    eval_cfg = EvalConfig(faithfulness_metric=faithfulness_metric)

    return AppConfig(
        llm=llm,
        rag=rag,
        weaviate=weaviate,
        guardrails=guardrails,
        eval=eval_cfg,
    )
