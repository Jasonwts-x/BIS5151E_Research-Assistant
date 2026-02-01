"""
Document Processing and Content Hashing.

Handles deterministic document chunking and ID generation.
Ensures rebuild produces identical IDs for identical content.

Key Features:
    - Content-hash based IDs (deterministic)
    - Stable chunk ordering
    - Metadata preservation
    - Automatic deduplication via ID collision detection
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from haystack.dataclasses import Document

from ..core.schema import SCHEMA_VERSION

logger = logging.getLogger(__name__)


@dataclass
class ProcessedChunk:
    """
    Represents a processed document chunk with metadata.
    
    Attributes:
        id: Deterministic content-hash based ID
        content: Chunk text content
        embedding: Vector embedding (optional)
        properties: Weaviate properties dict
    """

    id: str
    content: str
    embedding: Optional[List[float]]
    properties: Dict[str, Any]


class DocumentProcessor:
    """
    Processes documents into chunks with deterministic IDs.
    
    Attributes:
        chunk_size: Target size for chunks (in words)
        chunk_overlap: Overlap between chunks (in words)
    """

    def __init__(self, chunk_size: int = 350, chunk_overlap: int = 60):
        """
        Initialize processor.
        
        Args:
            chunk_size: Target size for chunks (in words)
            chunk_overlap: Overlap between chunks (in words)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[ProcessedChunk]:
        """
        Process documents into chunks with content-hash IDs.
        
        Args:
            documents: Haystack documents (already chunked by Haystack)
            embeddings: Optional pre-computed embeddings (must match documents)
            
        Returns:
            List of ProcessedChunk objects ready for Weaviate ingestion
        """
        if embeddings and len(embeddings) != len(documents):
            raise ValueError(
                f"Embeddings count ({len(embeddings)}) must match documents count ({len(documents)})"
            )

        processed = []
        doc_chunk_counts: Dict[str, int] = {}  # Track chunks per document

        # First pass: count chunks per document
        for doc in documents:
            doc_id = self._extract_document_id(doc)
            doc_chunk_counts[doc_id] = doc_chunk_counts.get(doc_id, 0) + 1

        # Second pass: process chunks
        for idx, doc in enumerate(documents):
            embedding = embeddings[idx] if embeddings else None
            chunk = self._process_single_chunk(doc, embedding, doc_chunk_counts)
            processed.append(chunk)

        logger.info(
            "Processed %d chunks from %d documents",
            len(processed),
            len(doc_chunk_counts),
        )

        return processed

    def _process_single_chunk(
        self,
        doc: Document,
        embedding: Optional[List[float]],
        doc_chunk_counts: Dict[str, int],
    ) -> ProcessedChunk:
        """
        Process a single chunk with metadata.
        
        Args:
            doc: Haystack document
            embedding: Optional embedding vector
            doc_chunk_counts: Dictionary of chunk counts per document
            
        Returns:
            ProcessedChunk with deterministic ID
        """
        meta = doc.meta or {}

        # Extract core metadata
        source = meta.get("source", "unknown")
        doc_id = self._extract_document_id(doc)
        chunk_index = meta.get("_split_id", 0)

        # Generate deterministic chunk ID
        chunk_id = self._generate_chunk_id(source, doc.content, chunk_index)

        # Build properties dict for Weaviate
        properties = {
            "content": doc.content.strip(),
            "source": source,
            "document_id": doc_id,
            "chunk_index": chunk_index,
            "chunk_hash": chunk_id,
            "total_chunks": doc_chunk_counts.get(doc_id, 1),
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "schema_version": SCHEMA_VERSION,
        }

        # Add optional metadata (ArXiv enrichment)
        if meta.get("authors"):
            properties["authors"] = meta["authors"]

        if meta.get("publication_date"):
            properties["publication_date"] = meta["publication_date"]

        if meta.get("arxiv_id"):
            properties["arxiv_id"] = meta["arxiv_id"]

        if meta.get("arxiv_category"):
            properties["arxiv_category"] = meta["arxiv_category"]

        if meta.get("abstract"):
            properties["abstract"] = meta["abstract"]

        return ProcessedChunk(
            id=chunk_id,
            content=doc.content,
            embedding=embedding,
            properties=properties,
        )

    def _extract_document_id(self, doc: Document) -> str:
        """
        Extract or generate document ID.
        
        Priority:
            1. Explicit document_id in metadata
            2. Hash of source filename
        
        Args:
            doc: Haystack document
            
        Returns:
            Document ID string
        """
        meta = doc.meta or {}

        if "document_id" in meta:
            return meta["document_id"]

        source = meta.get("source", "unknown")
        return hashlib.sha256(source.encode()).hexdigest()[:16]

    def _generate_chunk_id(self, source: str, content: str, chunk_index: int) -> str:
        """
        Generate deterministic chunk ID from content.
        
        Format: SHA-256 hash of (source + content + index)
        Truncated to 16 chars for readability
        
        This ensures:
            - Same content → same ID
            - Different content → different ID
            - Rebuild produces identical IDs
        
        Args:
            source: Source filename
            content: Chunk text content
            chunk_index: Sequential chunk index
            
        Returns:
            16-character deterministic ID
        """
        hash_input = f"{source}::{content}::{chunk_index}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    @staticmethod
    def chunk_documents_stable(
        documents: List[Document],
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[Document]:
        """
        Chunk documents with stable ordering.
        
        Uses Haystack's DocumentSplitter but ensures:
            - Documents are sorted by source (deterministic order)
            - Chunks maintain sequential IDs
        
        Args:
            documents: Raw documents to chunk
            chunk_size: Chunk size in words
            chunk_overlap: Overlap in words
            
        Returns:
            Chunked documents with stable _split_id metadata
        """
        from haystack.components.preprocessors import DocumentSplitter

        # Sort documents by source for deterministic ordering
        sorted_docs = sorted(documents, key=lambda d: d.meta.get("source", ""))

        # Chunk using Haystack
        splitter = DocumentSplitter(
            split_by="word",
            split_length=chunk_size,
            split_overlap=chunk_overlap,
        )

        result = splitter.run(documents=sorted_docs)
        chunks = result["documents"]

        logger.info("Chunked %d documents into %d chunks", len(sorted_docs), len(chunks))

        return chunks