"""
Abstract Base for Document Sources.

Defines interface for loading documents from various sources.
All document source implementations must inherit from this base class.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from haystack.dataclasses import Document


class DocumentSource(ABC):
    """
    Abstract base class for document sources.
    
    Implementations:
        - LocalFileSource: Load from local filesystem
        - ArXivSource: Fetch from ArXiv API
        - (Future: WebSource, DatabaseSource, etc.)
    """

    @abstractmethod
    def fetch(self, **kwargs) -> List[Document]:
        """
        Fetch documents from this source.
        
        Args:
            **kwargs: Source-specific parameters
            
        Returns:
            List of Haystack Document objects with metadata
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return human-readable source name for logging.
        
        Returns:
            Source name string (e.g., "LocalFiles", "ArXiv")
        """
        pass