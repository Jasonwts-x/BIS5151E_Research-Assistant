"""
RAG Pipeline - Refactored for Singleton Pattern

Separates index building (rare) from retrieval (frequent).
Uses lazy singleton pattern for efficient query handling.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.dataclasses import Document

from ...utils.config import load_config
from ..ingestion.engine import IngestionEngine
from ..sources import ArXivSource, LocalFileSource

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce httpx noise

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "raw"


@dataclass
class RAGPipeline:
    """
    RAG Pipeline with lazy singleton pattern.
    
    Two modes:
    1. Build mode (rare): RAGPipeline.build_index_from_local() / build_index_from_arxiv()
    2. Query mode (frequent): RAGPipeline.from_existing() - reuses existing index
    
    The query mode is used by the API/CrewAI and is cached as a singleton.
    """

    client: any  # Weaviate client
    retriever: any  # WeaviateHybridRetriever
    text_embedder: SentenceTransformersTextEmbedder
    collection_name: str

    @classmethod
    def build_index_from_local(
        cls,
        data_dir: Optional[Path] = None,
        pattern: str = "*",
    ) -> None:
        """
        Build index from local files.
        
        This is an INGESTION operation - run rarely.
        
        Args:
            data_dir: Directory containing documents (default: data/raw)
            pattern: File pattern to match (default: all files)
        """
        if data_dir is None:
            data_dir = DATA_DIR
        
        logger.info("Building index from local files: %s", data_dir)
        
        # Create ingestion engine
        engine = IngestionEngine()
        
        # Ingest from local source
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
        
        This is an INGESTION operation - run rarely.
        
        Args:
            query: ArXiv search query
            max_results: Number of papers to fetch
        """
        logger.info("Building index from ArXiv: query='%s', max=%d", query, max_results)
        
        # Create ingestion engine
        engine = IngestionEngine()
        
        # Ingest from ArXiv source
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

    @classmethod
    def from_existing(cls) -> "RAGPipeline":
        """
        Create pipeline connected to EXISTING Weaviate index.
        
        This is a QUERY operation - used frequently by API/CrewAI.
        Does NOT rebuild index.
        
        Returns:
            RAGPipeline instance ready for querying
        """
        cfg = load_config()
        
        # Connect to existing Weaviate
        client = cls._create_weaviate_client(cfg)
        
        # Get collection
        from .schema import RESEARCH_DOCUMENT_SCHEMA
        collection_name = RESEARCH_DOCUMENT_SCHEMA["class"]
        
        # Check if collection exists
        if not client.collections.exists(collection_name):
            raise RuntimeError(
                f"Collection '{collection_name}' does not exist in Weaviate!\n"
                f"Please build the index first:\n"
                f"  - python -m src.rag.cli ingest-local\n"
                f"  - python -m src.rag.cli ingest-arxiv <query>\n"
                f"  - POST /rag/ingest/local\n"
                f"  - POST /rag/ingest/arxiv"
            )
        
        # Create retriever
        try:
            from haystack_integrations.components.retrievers.weaviate import (
                WeaviateHybridRetriever,
            )
            from haystack_integrations.document_stores.weaviate import (
                WeaviateDocumentStore,
            )
        except ImportError:
            raise RuntimeError(
                "weaviate-haystack not installed. "
                "Install it: pip install weaviate-haystack"
            )
        
        # Document store
        store_kwargs = {"url": cfg.weaviate.url}
        if cfg.weaviate.api_key:
            from weaviate.auth import AuthApiKey
            store_kwargs["auth_client_secret"] = AuthApiKey(cfg.weaviate.api_key)
        
        store = WeaviateDocumentStore(**store_kwargs)
        
        # Hybrid retriever
        retriever = WeaviateHybridRetriever(document_store=store)
        
        # Text embedder (for queries)
        embedding_model = cfg.weaviate.embedding_model
        text_embedder = SentenceTransformersTextEmbedder(model=embedding_model)
        text_embedder.warm_up()
        
        logger.info("RAGPipeline connected to existing index (collection: %s)", collection_name)
        
        return cls(
            client=client,
            retriever=retriever,
            text_embedder=text_embedder,
            collection_name=collection_name,
        )

    def run(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Retrieve relevant documents for query.
        
        This is FAST - just searches existing index.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        logger.info("Retrieving top_k=%d for query='%s'", top_k, query)
        
        # Embed query
        emb_result = self.text_embedder.run(text=query)
        query_embedding = emb_result["embedding"]
        
        # Hybrid search
        result = self.retriever.run(
            query=query,
            query_embedding=query_embedding,
            top_k=top_k,
        )
        
        docs = result.get("documents", [])
        logger.info("Retrieved %d documents", len(docs))
        
        return docs

    @staticmethod
    def _create_weaviate_client(cfg):
        """Create Weaviate client from config."""
        import weaviate
        from weaviate.classes.init import Auth
        
        url = cfg.weaviate.url
        api_key = cfg.weaviate.api_key
        
        if api_key:
            # Cloud deployment with auth
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=Auth.api_key(api_key),
            )
        else:
            # Local deployment without auth
            # Parse host and port from URL
            url_clean = url.replace("http://", "").replace("https://", "")
            if ":" in url_clean:
                host, port_str = url_clean.split(":")
                port = int(port_str)
            else:
                host = url_clean
                port = 8080
            
            client = weaviate.connect_to_local(
                host=host,
                port=port,
            )
        
        return client


# ============================================================================
# Backward Compatibility (Deprecated)
# ============================================================================
# This method is kept for backward compatibility but should not be used.
# It will be removed in a future version.
# ============================================================================

def from_config_deprecated():
    """
    DEPRECATED: Use RAGPipeline.from_existing() instead.
    
    This old method rebuilds the index on every call (VERY slow).
    New code should use:
    - RAGPipeline.build_index_*() for ingestion
    - RAGPipeline.from_existing() for retrieval
    """
    logger.warning(
        "DEPRECATED: RAGPipeline.from_config() rebuilds index on every call. "
        "Use RAGPipeline.from_existing() for queries instead."
    )
    return RAGPipeline.from_existing()