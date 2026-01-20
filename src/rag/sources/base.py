"""
Abstract Base for Document Sources

Defines interface for loading documents from various sources.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from haystack.dataclasses import Document


class DocumentSource(ABC):
    """
    Abstract base class for document sources.
    
    Implementations: LocalFileSource, ArXivSource, etc.
    """

    @abstractmethod
    def fetch(self, **kwargs) -> List[Document]:
        """
        Fetch documents from this source.
        
        Returns:
            List of Haystack Document objects with metadata
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable source name for logging."""
        pass