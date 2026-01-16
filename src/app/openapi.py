from __future__ import annotations

from enum import StrEnum
from typing import Any


class APITag(StrEnum):
    SYSTEM = "system"
    RAG = "rag"
    OLLAMA = "ollama"


def openapi_tags() -> list[dict[str, Any]]:
    """
    Controls the tag list, ordering and descriptions in Swagger UI.
    """
    return [
        {
            "name": APITag.SYSTEM,
            "description": "Health, readiness, and basic service metadata.",
        },
        {
            "name": APITag.RAG,
            "description": "Retrieval-augmented generation endpoints.",
        },
        {
            "name": APITag.OLLAMA,
            "description": "Direct Ollama LLM access and model management.",
        },
    ]
