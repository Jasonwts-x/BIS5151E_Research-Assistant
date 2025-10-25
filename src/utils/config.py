from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "configs" / "app.yaml"


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "llama3"
    host: str = "http://localhost:11434"


@dataclass
class RAGConfig:
    chunk_size: int = 350
    chunk_overlap: int = 60
    top_k: int = 5


@dataclass
class AppConfig:
    llm: LLMConfig
    rag: RAGConfig


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config() -> AppConfig:
    load_dotenv(ROOT / ".env", override=False)

    y = _read_yaml(CONFIG_FILE)
    if not y:
        print(f"ℹ️  No configs/app.yaml found at {CONFIG_FILE}, using defaults/env only.")
        
    llm_y = (y.get("llm") or {})
    rag_y = (y.get("rag") or {})

    llm_model = os.getenv("LLM_MODEL", llm_y.get("model", "llama3"))
    llm_host = os.getenv("OLLAMA_HOST", llm_y.get(
        "host", "http://localhost:11434"))

    rag_chunk_size = int(
        os.getenv("RAG_CHUNK_SIZE", rag_y.get("chunk_size", 350)))
    rag_chunk_overlap = int(
        os.getenv("RAG_CHUNK_OVERLAP", rag_y.get("chunk_overlap", 60)))
    rag_top_k = int(os.getenv("RAG_TOP_K", rag_y.get("top_k", 5)))

    rag_chunk_size = max(1, rag_chunk_size)
    rag_chunk_overlap = max(0, rag_chunk_overlap)
    rag_top_k = max(1, rag_top_k)

    llm = LLMConfig(
        provider=llm_y.get("provider", "ollama"),
        model=llm_model,
        host=llm_host,
    )
    rag = RAGConfig(
        chunk_size=rag_chunk_size,
        chunk_overlap=rag_chunk_overlap,
        top_k=rag_top_k,
    )
    return AppConfig(llm=llm, rag=rag)
