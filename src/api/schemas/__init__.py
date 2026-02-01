"""
API Schemas.

Pydantic models for API requests and responses across all endpoint groups.

Organization:
    - system: Health, version, status schemas
    - research: Complete workflow request/response
    - crewai: Agent execution schemas
    - rag: Ingestion and retrieval schemas
    - ollama: LLM interaction schemas
    - eval: Evaluation metrics schemas
"""
from __future__ import annotations

from .crewai import (
    CrewAsyncRunResponse,
    CrewRunRequest,
    CrewRunResponse,
    CrewStatusResponse,
)
from .eval import (
    EvaluationRequest,
    EvaluationResponse,
    LeaderboardResponse,
)
from .ollama import (
    OllamaChatRequest,
    OllamaChatResponse,
    OllamaInfoResponse,
    OllamaModel,
    OllamaModelsResponse,
    OllamaPullRequest,
    OllamaPullResponse,
)
from .rag import (
    IngestArxivRequest,
    IngestLocalRequest,
    IngestionResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatsResponse,
    ResetIndexResponse,
)
from .research import (
    ResearchAsyncResponse,
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchStatusResponse,
)
from .system import (
    HealthResponse,
    ReadyResponse,
    VersionResponse,
)

__all__ = [
    # --- System ---
    "HealthResponse",
    "ReadyResponse",
    "VersionResponse",

    # --- Research ---
    "ResearchAsyncResponse",
    "ResearchQueryRequest",
    "ResearchQueryResponse",
    "ResearchStatusResponse",

    # --- CrewAI ---
    "CrewAsyncRunResponse",
    "CrewRunRequest",
    "CrewRunResponse",
    "CrewStatusResponse",

    # --- RAG ---
    "IngestArxivRequest",
    "IngestLocalRequest",
    "IngestionResponse",
    "RAGQueryRequest",
    "RAGQueryResponse",
    "RAGStatsResponse",
    "ResetIndexResponse",

    # --- Ollama ---
    "OllamaChatRequest",
    "OllamaChatResponse",
    "OllamaInfoResponse",
    "OllamaModel",
    "OllamaModelsResponse",
    "OllamaPullRequest",
    "OllamaPullResponse",

    # --- Evaluation ---
    "EvaluationRequest",
    "EvaluationResponse",
    "LeaderboardResponse",
]