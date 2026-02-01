"""
FastAPI Dependencies.

Dependency injection for services and configuration used across API endpoints.
Implements singleton pattern for expensive resources (RAG service, config).

Architecture Note:
    Uses lru_cache for singleton instances to avoid redundant initialization.
    Future dependencies (Weaviate client, Ollama client) are stubbed for later steps.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from ..rag.core import RAGService
from ..utils.config import AppConfig, load_config

logger = logging.getLogger(__name__)


@lru_cache
def get_config() -> AppConfig:
    """
    Get application configuration (singleton).
    
    Returns:
        AppConfig: Application configuration instance
    """
    return load_config()


@lru_cache
def get_rag_service() -> RAGService:
    """
    Get RAG service instance (singleton).
    
    Initializes RAGPipeline connection to Weaviate on first call.
    Subsequent calls return the same instance.
    
    Returns:
        RAGService: RAG service instance for document retrieval
    """
    return RAGService()


# ---------------------------------------------------------------------------
# Placeholders for future dependency wiring (NOT IMPLEMENTED YET)
# ---------------------------------------------------------------------------
# NOTE: We keep these as stubs to avoid forcing architectural refactors.
# We'll implement them later when the surrounding components are stable.
# ---------------------------------------------------------------------------


def get_weaviate_client() -> Any:  # pragma: no cover
    """
    Placeholder for Weaviate client dependency.

    Implement in Step E (Harden RAG + deterministic ingestion + stable IDs).
    At that point we decide:
        - which client library to use (weaviate-client v4, raw HTTP, etc.)
        - lifecycle: startup/shutdown hooks vs simple lazy init
        - how RAGPipeline/RAGService receives the client (dependency injection)

    Expected future usage:
        - used by ingestion endpoints (/rag/ingest)
        - used by admin/debug endpoints (schema/status)
    """
    raise NotImplementedError("Implement in Step E (Weaviate hardening).")


def get_ollama_base_url() -> str:  # pragma: no cover
    """
    Placeholder for Ollama base URL.

    Implement in Step C (Ollama compose service). For now, Ollama is referenced
    via config (OLLAMA_HOST). After Step C we may:
        - validate connectivity here
        - provide a stable base URL for an Ollama client wrapper
    
    Returns:
        str: Ollama base URL from configuration
    """
    cfg = get_config()
    return cfg.llm.host


def get_ollama_client() -> Any:  # pragma: no cover
    """
    Placeholder for Ollama client.

    Implement after Step C once we decide on:
        - direct HTTP calls
        - an SDK/wrapper
        - retry/timeouts and error mapping
    """
    raise NotImplementedError("Implement after Step C (Ollama service).")


def get_crew_runner() -> Any:  # pragma: no cover
    """
    Placeholder for CrewAI runner.

    Implement in Step D (CrewAI service). Likely returns:
        - a client for a CrewAI service
        - or a local runner interface if CrewAI runs in-process (less likely for us)
    """
    raise NotImplementedError("Implement in Step D (CrewAI).")


def get_n8n_client() -> Any:  # pragma: no cover
    """
    Placeholder for n8n client (optional).

    Only implement if we decide the API should trigger n8n workflows directly.
    Otherwise, n8n will call the API, not the other way around.
    """
    raise NotImplementedError("Implement only if needed.")


# ---------------------------------------------------------------------------
# Reminder: update these placeholders when we reach future steps
# - Step C: implement get_ollama_client (or minimal wrapper)
# - Step D: implement get_crew_runner
# - Step E: implement get_weaviate_client + ingestion wiring
# ---------------------------------------------------------------------------