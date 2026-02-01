"""
Document Sources.

Abstraction for loading documents from various sources.
Provides a unified interface for fetching documents from local files, ArXiv, etc.
"""
from __future__ import annotations

from .arxiv import ArXivSource
from .base import DocumentSource
from .local import LocalFileSource

__all__ = [
    "DocumentSource",
    "LocalFileSource",
    "ArXivSource",
]