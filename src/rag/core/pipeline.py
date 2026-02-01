"""
RAG Pipeline - Singleton Pattern.

Separates index building (rare) from retrieval (frequent) using lazy singleton pattern.
Optimized for local LLM performance with smart context truncation.

Architecture:
    - Build mode: RAGPipeline.build_index_from_local() / build_index_from_arxiv()
    - Query mode: RAGPipeline.from_existing() (reuses existing index, singleton cached)

The query mode is used by API/CrewAI services and maintains a single pipeline instance.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.dataclasses import Document

from ...utils.config import load_config
from ..ingestion.engine import IngestionEngine
from ..sources import ArXivSource, LocalFileSource

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "raw"


@dataclass
class RAGPipeline:
    """
    RAG Pipeline with lazy singleton pattern.
    
    Attributes:
        client: Weaviate client instance
        retriever: Weaviate retriever (legacy, not currently used)
        text_embedder: SentenceTransformers embedder for query embedding
        collection_name: Weaviate collection name (default: "ResearchDocument")
    """

    client: any
    retriever: any
    text_embedder: SentenceTransformersTextEmbedder
    collection_name: str

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self) -> None:
        """
        Close Weaviate client and cleanup resources.
        
        Should be called when pipeline is no longer needed to prevent resource leaks.
        """
        if hasattr(self, 'client') and self.client is not None:
            try:
                self.client.close()
                logger.debug("Weaviate client closed")
            except Exception as e:
                logger.warning("Error closing Weaviate client: %s", e)

    @staticmethod
    def _create_weaviate_client(cfg):
        """
        Create Weaviate client based on configuration.
        
        Supports both local and cloud deployments.
        FIXED: Uses connect_to_custom to ensure correct gRPC communication in Docker.
        
        Args:
            cfg: Application configuration with Weaviate settings
            
        Returns:
            Connected Weaviate client
        """
        import weaviate
        from weaviate.classes.init import Auth
        from urllib.parse import urlparse

        url = cfg.weaviate.url
        api_key = cfg.weaviate.api_key

        if api_key:
            # Cloud deployment with authentication
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=Auth.api_key(api_key),
            )
        else:
            # Local / Docker deployment
            parsed = urlparse(url if url.startswith('http') else f'http://{url}')
            host = parsed.hostname or 'localhost'
            port = parsed.port or 8080
            grpc_port = 50051  # Standard gRPC port for Weaviate

            logger.info("Connecting to Weaviate at %s (HTTP:%d, gRPC:%d)", host, port, grpc_port)

            # Use connect_to_custom to explicitly set gRPC host/port.
            # In Docker, the host for gRPC is the same as HTTP (e.g., 'weaviate').
            client = weaviate.connect_to_custom(
                http_host=host,
                http_port=port,
                http_secure=False,
                grpc_host=host,     # WICHTIG: Muss im Docker-Netz explizit gesetzt sein
                grpc_port=grpc_port,
                grpc_secure=False
            )

        logger.info("Connected to Weaviate successfully")
        return client

    @classmethod
    def from_existing(cls) -> "RAGPipeline":
        """
        Connect to existing Weaviate index for querying.
        
        Auto-creates schema if collection doesn't exist yet.
        This is the primary method for query operations (API/CrewAI).
        
        Returns:
            RAGPipeline instance ready for querying
            
        Raises:
            RuntimeError: If Weaviate connection fails
        """
        cfg = load_config()

        logger.info("Connecting to Weaviate index at %s", cfg.weaviate.url)

        # Connect to Weaviate
        client = cls._create_weaviate_client(cfg)

        try:
            # Get collection name from schema definition
            from .schema import RESEARCH_DOCUMENT_SCHEMA
            collection_name = RESEARCH_DOCUMENT_SCHEMA["class"]

            # Check if collection exists, create if needed
            if not client.collections.exists(collection_name):
                logger.warning(
                    "Collection '%s' does not exist. Creating schema automatically...",
                    collection_name
                )

                # Auto-create schema using SchemaManager
                from .schema import SchemaManager
                schema_manager = SchemaManager(
                    client=client,
                    allow_reset=False
                )
                schema_manager.ensure_schema()

                logger.info("✓ Collection '%s' created successfully", collection_name)
            else:
                logger.info("✓ Collection '%s' exists", collection_name)

            # Initialize text embedder for queries
            embedding_model = cfg.weaviate.embedding_model
            text_embedder = SentenceTransformersTextEmbedder(model=embedding_model)
            text_embedder.warm_up()

            logger.info("RAGPipeline connected to existing index (collection: %s)", collection_name)

            return cls(
                client=client,
                retriever=None,  # We use raw Weaviate client for queries
                text_embedder=text_embedder,
                collection_name=collection_name,
            )

        except Exception as e:
            # Cleanup client on error to prevent resource leak
            logger.error("Failed to initialize RAGPipeline: %s", e)
            try:
                client.close()
                logger.debug("Weaviate client closed after error")
            except Exception as close_error:
                logger.warning("Failed to close Weaviate client: %s", close_error)
            raise RuntimeError(
                f"Failed to initialize RAGPipeline: {e}\n"
                f"Collection: {collection_name}"
            ) from e

    @classmethod
    def build_index_from_local(
        cls,
        data_dir: Optional[Path] = None,
        pattern: str = "*",
    ) -> None:
        """
        Build index from local files.
        
        This is an ingestion operation - use sparingly. For queries, use from_existing().
        
        Args:
            data_dir: Directory containing documents (default: data/raw)
            pattern: Glob pattern for file matching (default: all files)
        """
        if data_dir is None:
            data_dir = DATA_DIR

        logger.info("Building index from local files: %s", data_dir)

        # Use context manager to ensure cleanup
        with IngestionEngine() as engine:
            source = LocalFileSource(data_dir)
            result = engine.ingest_from_source(source, pattern=pattern)

            logger.info(
                "Index build complete: %d docs, %d chunks ingested",
                result.documents_loaded,
                result.chunks_ingested,
            )

            if result.errors:
                logger.warning("Errors during ingestion: %s", result.errors)

    @classmethod
    def build_index_from_arxiv(
        cls,
        query: str,
        max_results: int = 5,
    ) -> None:
        """
        Build index from ArXiv papers.
        
        This is an ingestion operation - use sparingly. For queries, use from_existing().
        
        Args:
            query: ArXiv search query
            max_results: Maximum number of papers to fetch
        """
        logger.info("Building index from ArXiv: query='%s', max=%d", query, max_results)

        # Use context manager to ensure cleanup
        with IngestionEngine() as engine:
            source = ArXivSource()
            result = engine.ingest_from_source(
                source,
                query=query,
                max_results=max_results,
            )

            logger.info(
                "Index build complete: %d papers, %d chunks ingested",
                result.documents_loaded,
                result.chunks_ingested,
            )

            if result.errors:
                logger.warning("Errors during ingestion: %s", result.errors)

    def run(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Retrieve relevant documents using Hybrid Search.
        
        Implements smart truncation to prevent context overflow for local LLMs.
        Uses Weaviate's hybrid search (BM25 + semantic) with alpha=0.55.
        
        Args:
            query: Search query
            top_k: Number of results to return (default: 5)
            
        Returns:
            List of relevant documents with optimized content length
        """
        logger.info("Retrieving top_k=%d for query='%s'", top_k, query)

        # Generate query embedding
        emb_result = self.text_embedder.run(text=query)
        query_embedding = emb_result["embedding"]

        # Get Weaviate collection
        collection = self.client.collections.get(self.collection_name)

        # DIAGNOSTIC: Check if collection has any documents before querying
        try:
            # Quick sanity check - fetch 1 object to verify collection has data
            # This requires a working gRPC connection!
            test_fetch = collection.query.fetch_objects(limit=1)
            collection_has_data = test_fetch and len(test_fetch.objects) > 0
            logger.info(
                "Pre-query diagnostic: collection '%s' has data: %s",
                self.collection_name,
                collection_has_data
            )
            if not collection_has_data:
                logger.warning(
                    "Collection '%s' appears empty! No documents will be retrieved.",
                    self.collection_name
                )
        except Exception as diag_error:
            logger.warning("Pre-query diagnostic failed: %s", diag_error)

        # Hybrid search: alpha=0.55 favors vector search over BM25
        # This balances semantic understanding with keyword matching
        response = collection.query.hybrid(
            query=query,
            vector=query_embedding,
            alpha=0.55,
            limit=top_k,
            return_metadata=['score'],
        )

        # DIAGNOSTIC: Log response details
        result_count = len(response.objects) if response and response.objects else 0
        logger.info("Hybrid search returned %d results (requested top_k=%d)", result_count, top_k)

        # Convert Weaviate objects to Haystack Documents with smart truncation
        docs = []

        # Smart truncation configuration
        # Target: ~600 tokens per chunk, 5 chunks = ~3000 tokens total context
        MAX_CHARS_PER_CHUNK = 2500

        for obj in response.objects:
            props = obj.properties
            raw_content = props.get('content', '')

            # Clean whitespace: newlines/tabs → single space
            # This saves massive tokens in PDFs with bad formatting
            clean_content = re.sub(r'\s+', ' ', raw_content).strip()

            # Smart truncate if needed
            if len(clean_content) > MAX_CHARS_PER_CHUNK:
                # Cut at limit
                truncated = clean_content[:MAX_CHARS_PER_CHUNK]
                # Try to find last sentence end for clean cut
                last_period = truncated.rfind('.')
                if last_period > MAX_CHARS_PER_CHUNK * 0.8:  # At least 80% through
                    clean_content = truncated[:last_period + 1]
                else:
                    clean_content = truncated + "..."

            # Create Haystack Document
            doc = Document(
                content=clean_content,
                meta={
                    'source': props.get('source', 'unknown'),
                    'chunk_index': props.get('chunk_index', 0),
                    'document_id': props.get('document_id', ''),
                    'authors': props.get('authors', []),
                    'arxiv_id': props.get('arxiv_id', ''),
                },
                score=obj.metadata.score if hasattr(obj.metadata, 'score') else None,
            )
            docs.append(doc)

        logger.info("Retrieved %d documents (smart truncation applied)", len(docs))

        return docs


# Legacy compatibility function
def get_rag_pipeline():
    """
    DEPRECATED: Use RAGPipeline.from_existing() instead.
    
    Returns:
        RAGPipeline instance
    """
    logger.warning("DEPRECATED: Use RAGPipeline.from_existing() for queries.")
    return RAGPipeline.from_existing()