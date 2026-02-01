"""
Ingestion Engine.

Orchestrates the full ingestion pipeline from documents to indexed chunks.

Pipeline Steps:
    1. Load documents from source (LocalFileSource, ArXivSource, etc.)
    2. Chunk documents (stable ordering for determinism)
    3. Generate embeddings (sentence-transformers)
    4. Process chunks (generate content-hash IDs)
    5. Write to Weaviate (skip duplicates)
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from typing import List, Optional

from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.dataclasses import Document

from ...utils.config import load_config
from ..core.schema import SchemaManager
from ..sources.base import DocumentSource
from .processor import DocumentProcessor, ProcessedChunk

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


@dataclass
class IngestionResult:
    """
    Result of ingestion operation.
    
    Attributes:
        source: Source name (e.g., "LocalFiles", "ArXiv")
        documents_loaded: Number of documents fetched
        chunks_created: Number of chunks created
        chunks_ingested: Number of chunks written to Weaviate
        chunks_skipped: Number of duplicate chunks skipped
        errors: List of error messages
        success: Whether ingestion completed successfully
        papers: List of paper metadata (ArXiv only)
    """

    source: str
    documents_loaded: int
    chunks_created: int
    chunks_ingested: int
    chunks_skipped: int
    errors: List[str]
    success: bool
    papers: Optional[List[dict]] = None


class IngestionEngine:
    """
    Orchestrates document ingestion into Weaviate.
    
    Workflow:
        1. Fetch documents from source
        2. Chunk documents (stable ordering)
        3. Generate embeddings
        4. Process chunks (generate content-hash IDs)
        5. Write to Weaviate (skip duplicates)
    
    Attributes:
        config: Application configuration
        client: Weaviate client instance
        schema_manager: Manages Weaviate schema
        processor: Handles document chunking and ID generation
        embedder: Generates embeddings for chunks
    """

    def __init__(self, weaviate_client=None):
        """
        Initialize ingestion engine.
        
        Args:
            weaviate_client: Weaviate client (if None, creates new one)
        """
        self.config = load_config()

        # Weaviate client
        if weaviate_client is None:
            weaviate_client = self._create_weaviate_client()
        self.client = weaviate_client

        # Schema manager
        allow_reset = self.config.rag.allow_schema_reset
        self.schema_manager = SchemaManager(
            client=self.client,
            allow_reset=allow_reset,
        )

        # Ensure schema exists
        self.schema_manager.ensure_schema()

        # Document processor
        self.processor = DocumentProcessor(
            chunk_size=self.config.rag.chunk_size,
            chunk_overlap=self.config.rag.chunk_overlap,
        )

        # Embedder
        embedding_model = self.config.weaviate.embedding_model
        self.embedder = SentenceTransformersDocumentEmbedder(model=embedding_model)
        self.embedder.warm_up()

        logger.info("IngestionEngine initialized with embedding model: %s", embedding_model)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()
        return False

    def close(self) -> None:
        """
        Close Weaviate client and cleanup resources.
        
        Should be called when engine is no longer needed.
        """
        if hasattr(self, 'client') and self.client is not None:
            try:
                self.client.close()
                logger.debug("IngestionEngine: Weaviate client closed")
            except Exception as e:
                logger.warning("IngestionEngine: Error closing Weaviate client: %s", e)

    def _create_weaviate_client(self):
        """
        Create Weaviate client based on configuration.
        
        Supports both local and cloud deployments.
        FIXED: Uses connect_to_custom to ensure correct gRPC communication in Docker.
        
        Returns:
            Connected Weaviate client
        """
        import weaviate
        from weaviate.classes.init import Auth
        from urllib.parse import urlparse

        url = self.config.weaviate.url
        api_key = self.config.weaviate.api_key

        if api_key:
            # Cloud deployment with auth
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=Auth.api_key(api_key),
            )
        else:
            # Local / Docker deployment
            parsed = urlparse(url if url.startswith('http') else f'http://{url}')
            host = parsed.hostname or 'localhost'
            port = parsed.port or 8080
            grpc_port = 50051 # Standard gRPC port for Weaviate

            logger.info("Connecting to Weaviate at %s (HTTP:%d, gRPC:%d)", host, port, grpc_port)

            # FIXED: Use connect_to_custom to explicitly set gRPC host/port.
            # connect_to_local often fails inside Docker containers because it 
            # implies 'localhost' for gRPC, but we need to talk to the 'weaviate' service.
            client = weaviate.connect_to_custom(
                http_host=host,
                http_port=port,
                http_secure=False,
                grpc_host=host,     # WICHTIG: Muss im Docker-Netz explizit auf 'weaviate' zeigen
                grpc_port=grpc_port,
                grpc_secure=False
            )

            logger.info("Connected to Weaviate successfully")
            return client

    def ingest_from_source(
        self,
        source: DocumentSource,
        **source_kwargs,
    ) -> IngestionResult:
        """
        Ingest documents from a source.
        
        Args:
            source: Document source (LocalFileSource, ArXivSource, etc.)
            **source_kwargs: Arguments to pass to source.fetch()
            
        Returns:
            IngestionResult with statistics
        """
        logger.info("Starting ingestion from source: %s", source.get_source_name())

        errors = []

        try:
            # Step 1: Fetch documents
            documents = source.fetch(**source_kwargs)

            if not documents:
                logger.warning("No documents fetched from source")
                return IngestionResult(
                    source=source.get_source_name(),
                    documents_loaded=0,
                    chunks_created=0,
                    chunks_ingested=0,
                    chunks_skipped=0,
                    errors=["No documents found"],
                    success=False,
                )

            logger.info("Fetched %d documents from source", len(documents))

            # Step 2: Chunk documents (stable ordering for determinism)
            chunks = self.processor.chunk_documents_stable(
                documents=documents,
                chunk_size=self.config.rag.chunk_size,
                chunk_overlap=self.config.rag.chunk_overlap,
            )

            logger.info("Created %d chunks from %d documents", len(chunks), len(documents))

            # Step 3: Generate embeddings
            embedded_result = self.embedder.run(documents=chunks)
            embedded_chunks = embedded_result["documents"]

            # Extract embeddings
            embeddings = [doc.embedding for doc in embedded_chunks]

            logger.info("Generated embeddings for %d chunks", len(embeddings))

            # Step 4: Process chunks (generate IDs)
            processed = self.processor.process_documents(
                documents=chunks,
                embeddings=embeddings,
            )

            # Step 5: Write to Weaviate
            ingested, skipped = self._write_to_weaviate(processed)

            logger.info(
                "Ingestion complete: %d ingested, %d skipped (duplicates)",
                ingested,
                skipped,
            )

            try:
                collection = self.client.collections.get(self.schema_manager.collection_name)
                # This fetch requires working gRPC!
                test_fetch = collection.query.fetch_objects(limit=5)
                actual_count = len(test_fetch.objects) if test_fetch and test_fetch.objects else 0
                logger.info("POST-INGESTION VERIFICATION: Collection now has %d documents (sampled)", actual_count)
            except Exception as verify_error:
                logger.warning("Post-ingestion verification failed: %s", verify_error)            

            return IngestionResult(
                source=source.get_source_name(),
                documents_loaded=len(documents),
                chunks_created=len(chunks),
                chunks_ingested=ingested,
                chunks_skipped=skipped,
                errors=errors,
                success=True,
            )

        except Exception as e:
            logger.exception("Ingestion failed")
            errors.append(str(e))
            return IngestionResult(
                source=source.get_source_name(),
                documents_loaded=0,
                chunks_created=0,
                chunks_ingested=0,
                chunks_skipped=0,
                errors=errors,
                success=False,
            )

    def _write_to_weaviate(self, chunks: List[ProcessedChunk]) -> tuple[int, int]:
        """
        Write processed chunks to Weaviate with deduplication.
        
        Uses batch insertion for efficiency. Skips chunks with duplicate IDs.
        
        Args:
            chunks: List of processed chunks with IDs and embeddings
            
        Returns:
            Tuple of (ingested_count, skipped_count)
        """
        collection = self.client.collections.get(self.schema_manager.collection_name)

        ingested = 0
        skipped = 0

        # Batch insert for efficiency
        # WARNING: In Weaviate v4 Python client, this relies heavily on gRPC.
        # If gRPC is not connected correctly, this might fail silently or hang.
        with collection.batch.dynamic() as batch:
            for chunk in chunks:
                try:
                    batch.add_object(
                        properties=chunk.properties,
                        vector=chunk.embedding,
                        uuid=chunk.id,  # Use content-hash as UUID for deduplication
                    )
                    ingested += 1
                except Exception as e:
                    # Duplicate ID or other error
                    if "already exists" in str(e).lower() or "uuid" in str(e).lower():
                        skipped += 1
                        logger.debug("Skipping duplicate chunk: %s", chunk.id)
                    else:
                        logger.warning("Failed to ingest chunk %s: %s", chunk.id, e)

        return ingested, skipped

    def clear_index(self) -> None:
        """
        Clear all documents from index.
        
        WARNING: This deletes all data and recreates the schema!
        """
        logger.warning("Clearing index - all documents will be deleted!")

        self.schema_manager._delete_schema()
        self.schema_manager._create_schema()

        logger.info("Index cleared successfully")

    def get_stats(self):
        """
        Get index statistics.
        
        Returns:
            Dictionary with collection name, schema version, document count, etc.
        """
        return self.schema_manager.get_stats()