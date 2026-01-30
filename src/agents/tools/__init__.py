"""
CrewAI Tools

Custom tools that agents can use during execution.
Tools provide agents with specific capabilities beyond LLM generation.
"""
from __future__ import annotations

from .citation_validator import validate_citation
from .text_analyzer import analyze_text_quality

__all__ = [
    "validate_citation",
    "analyze_text_quality",
]