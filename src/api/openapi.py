"""
OpenAPI Configuration.

Defines API metadata, tags, and documentation structure for the gateway.

Architecture:
    - APITag enum: Organizes endpoints into logical groups
    - openapi_tags(): Provides descriptions for each tag group
    - Order determines display order in /docs UI
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any


class APITag(StrEnum):
    """
    API endpoint tags for OpenAPI documentation.
    
    Used to organize endpoints into logical groups in the Swagger UI.
    """

    SYSTEM = "system"
    RESEARCH = "research"
    CREWAI = "crewai"
    OLLAMA = "ollama"
    EVAL = "eval"
    RAG = "rag"


def openapi_tags() -> list[dict[str, Any]]:
    """
    Return OpenAPI tags with descriptions.
    
    Tags organize endpoints in the API documentation (/docs).
    Order here determines display order in the Swagger UI.
    
    Returns:
        List of tag dictionaries with name and description
    """
    return [
        {
            "name": APITag.SYSTEM,
            "description": (
                "System-related endpoints. "
                "System health, version, and status endpoints",
            )
        },
        {
            "name": APITag.RESEARCH,
            "description": (
                "Primary research endpoints: Complete RAG + multi-agent workflow. "
                "These are the main user-facing endpoints for generating research summaries."
            ),
        },
        {
            "name": APITag.CREWAI,
            "description": (
                "CrewAI multi-agent service endpoints. "
                "Provides direct access to agent execution without RAG integration."
            ),
        },
        {
            "name": APITag.OLLAMA,
            "description": (
                "Ollama LLM service endpoints. "
                "Model management and direct LLM interaction."
            ),
        },
        {
            "name": APITag.EVAL,
            "description": (
                "Evaluation and quality metrics endpoints. "
                "TruLens monitoring, guardrails, and performance tracking."
            ),
        },
        {
            "name": APITag.RAG,
            "description": (
                "Retrieval-Augmented Generation endpoints. "
                "Document ingestion, vector search, and index management."
            ),
        },
    ]