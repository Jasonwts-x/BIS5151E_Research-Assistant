"""
RAG Pipeline - Singleton Pattern
 
Separates index building (rare) from retrieval (frequent).
Uses lazy singleton pattern for efficient query handling.
Optimized for local LLM performance (Smart Context Truncation).
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
   
    Two modes:
    1. Build mode (rare): RAGPipeline.build_index_from_local() / build_index_from_arxiv()
    2. Query mode (frequent): RAGPipeline.from_existing() - reuses existing index
   
    The query mode is used by the API/CrewAI and is cached as a singleton.
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
 
    def close(self):
        """Close Weaviate client and cleanup resources"""
        if hasattr(self, 'client') and self.client is not None:
            try:
                self.client.close()
                logger.debug("Weaviate client closed")
            except Exception as e:
                logger.warning("Error closing Weaviate client: %s", e)
 
    @classmethod
    def from_existing(cls) -> "RAGPipeline":
        """
        Connect to existing Weaviate index for querying.
    
        Auto-creates schema if collection doesn't exist yet.
        This is a QUERY operation - used frequently by API/CrewAI.
    
        Returns:
            RAGPipeline instance ready for querying
        
        Raises:
            RuntimeError: If Weaviate connection fails
        """
        cfg = load_config()
    
        logger.info("Connecting to Weaviate index at %s", cfg.weaviate.url)
    
        # Connect to Weaviate
        client = cls._create_weaviate_client(cfg)

        # Initialize collection_name with default before try block
        collection_name = "ResearchDocument"  # Default fallback        

        try:
            # Get collection name from schema definition
            from ..ingestion.schema import RESEARCH_DOCUMENT_SCHEMA
            collection_name = RESEARCH_DOCUMENT_SCHEMA["class"]
        
            # Check if collection exists
            if not client.collections.exists(collection_name):
                logger.warning(
                    "Collection '%s' does not exist. Creating schema automatically...",
                    collection_name
                )
            
                # Auto-create schema
                from ..ingestion.schema import SchemaManager
                schema_manager = SchemaManager(
                    client=client,
                    collection_name=collection_name,
                    embedding_model=cfg.weaviate.embedding_model
                )
                schema_manager.create_schema()
            
                logger.info("✓ Collection '%s' created successfully", collection_name)
            else:
                logger.info("✓ Collection '%s' exists", collection_name)
        
            # Text embedder (for queries)
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
        Includes SMART TRUNCATION to prevent context overflow.
   
        Args:
            query: Search query
            top_k: Number of results to return (Default 5)
       
        Returns:
            List of relevant documents (optimized size)
        """
        logger.info("Retrieving top_k=%d for query='%s'", top_k, query)
   
        # Embed query
        emb_result = self.text_embedder.run(text=query)
        query_embedding = emb_result["embedding"]
   
        # Get collection
        collection = self.client.collections.get(self.collection_name)
   
        # Hybrid search using raw Weaviate client
        # alpha=0.55 favors vector search (semantic) over BM25 (keyword)
        response = collection.query.hybrid(
            query=query,
            vector=query_embedding,
            alpha=0.55,
            limit=top_k,
            return_metadata=['score'],
        )
   
        # Convert Weaviate objects to Haystack Documents with optimization
        docs = []
       
        # --- CONFIGURATION FOR SMART TRUNCATION ---
        MAX_CHARS_PER_CHUNK = 2500  # ~600 Tokens. 5 chunks * 600 = 3000 tokens total context.
       
        for obj in response.objects:
            props = obj.properties
            raw_content = props.get('content', '')
           
            # 1. Clean whitespace (newlines/tabs -> single space)
            # This saves massive amounts of tokens in PDFs with bad formatting
            clean_content = re.sub(r'\s+', ' ', raw_content).strip()
           
            # 2. Smart Truncate
            if len(clean_content) > MAX_CHARS_PER_CHUNK:
                # Cut at limit
                truncated = clean_content[:MAX_CHARS_PER_CHUNK]
                # Try to find the last sentence end to cut cleanly
                last_period = truncated.rfind('.')
                if last_period > MAX_CHARS_PER_CHUNK * 0.8: # Only cut if period is near the end
                    clean_content = truncated[:last_period+1] + " ... [content truncated]"
                else:
                    clean_content = truncated + " ... [content truncated]"
       
            # Create Haystack Document
            doc = Document(
                content=clean_content,
                meta={
                    'source': props.get('source', ''),
                    'document_id': props.get('document_id', ''),
                    'chunk_index': props.get('chunk_index', 0),
                    'total_chunks': props.get('total_chunks', 0),
                    'authors': props.get('authors', []),
                    'publication_date': props.get('publication_date', ''),
                    'title': props.get('title', ''),
                },
                score=obj.metadata.score if obj.metadata and hasattr(obj.metadata, 'score') else None,
            )
            docs.append(doc)
   
        logger.info("Retrieved %d documents (optimized)", len(docs))
   
        return docs
 
    @staticmethod
    def _create_weaviate_client(cfg):
        """Create Weaviate client from config."""
        import weaviate
        from weaviate.classes.init import Auth
        from urllib.parse import urlparse
       
        url = cfg.weaviate.url
        api_key = cfg.weaviate.api_key
       
        try:
            if api_key:
                client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=url,
                    auth_credentials=Auth.api_key(api_key),
                )
            else:
                parsed = urlparse(url if url.startswith('http') else f'http://{url}')
                host = parsed.hostname or 'localhost'
                port = parsed.port or 8080
 
                client = weaviate.connect_to_local(
                    host=host,
                    port=port
                    # Timeout entfernt für Kompatibilität
                )
            return client
        except Exception as e:
            logger.error("Failed to connect to Weaviate: %s", e)
            raise
 
# ============================================================================
# Backward Compatibility (Deprecated)
# ============================================================================
 
def from_config_deprecated():
    """DEPRECATED: Use RAGPipeline.from_existing() instead."""
    logger.warning("DEPRECATED: Use RAGPipeline.from_existing() for queries.")
    return RAGPipeline.from_existing()