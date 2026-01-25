"""
Ingestion Engine

Orchestrates the full ingestion pipeline:
1. Load documents from source
2. Chunk documents
3. Generate embeddings
4. Write to Weaviate with content-hash IDs
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
logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce httpx noise

@dataclass
class IngestionResult:
    """Result of ingestion operation."""

    source_name: str
    documents_loaded: int
    chunks_created: int
    chunks_ingested: int
    chunks_skipped: int  # Duplicates
    errors: List[str]


class IngestionEngine:
    """
    Orchestrates document ingestion into Weaviate.
    
    Workflow:
    1. Fetch documents from source
    2. Chunk documents (stable ordering)
    3. Generate embeddings
    4. Process chunks (generate content-hash IDs)
    5. Write to Weaviate (skip duplicates)
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
                    source_name=source.get_source_name(),
                    documents_loaded=0,
                    chunks_created=0,
                    chunks_ingested=0,
                    chunks_skipped=0,
                    errors=["No documents found"],
                )
            
            logger.info("Fetched %d documents from source", len(documents))
            
            # Step 2: Chunk documents (stable ordering)
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
            
            return IngestionResult(
                source_name=source.get_source_name(),
                documents_loaded=len(documents),
                chunks_created=len(chunks),
                chunks_ingested=ingested,
                chunks_skipped=skipped,
                errors=errors,
            )
            
        except Exception as e:
            logger.exception("Ingestion failed")
            errors.append(str(e))
            return IngestionResult(
                source_name=source.get_source_name(),
                documents_loaded=0,
                chunks_created=0,
                chunks_ingested=0,
                chunks_skipped=0,
                errors=errors,
            )

    def _write_to_weaviate(
        self,
        chunks: List[ProcessedChunk],
    ) -> tuple[int, int]:
        """
        Write chunks to Weaviate.
        
        Uses content-hash IDs for automatic deduplication:
        - If ID exists: Skip (idempotent)
        - If ID new: Insert
        
        Returns:
            Tuple of (ingested_count, skipped_count)
        """
        from weaviate.util import generate_uuid5
        
        collection = self.client.collections.get(self.schema_manager.collection_name)
        
        ingested = 0
        skipped = 0

        # Check existing UUIDs first
        existing_uuids = set()
        for chunk in chunks:
            uuid = generate_uuid5(chunk.id)
            try:
                # Try to fetch - if it exists, it will return an object
                obj = collection.query.fetch_object_by_id(uuid)
                if obj:
                    existing_uuids.add(uuid)
                    skipped += 1
            except Exception:
                # Doesn't exist, will insert
                pass

        logger.info("Found %d existing chunks, will skip them", len(existing_uuids))
        
        # Batch insert
        with collection.batch.dynamic() as batch:
            for chunk in chunks:
                uuid = generate_uuid5(chunk.id)
                    
                if uuid in existing_uuids:
                        continue

                try:
                    batch.add_object(
                        properties=chunk.properties,
                        uuid=uuid,
                        vector=chunk.embedding,
                    )
                    
                    ingested += 1
                    
                except Exception as e:
                    logger.warning("Failed to insert chunk %s: %s", chunk.id, e)
                    skipped += 1
        
            return ingested, skipped

    def _create_weaviate_client(self):
        """Create Weaviate client from config."""
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
            # Local deployment without auth
            parsed = urlparse(url if url.startswith('http') else f'http://{url}')
            host = parsed.hostname or 'localhost'
            port = parsed.port or 8080

            logger.info("Connecting to Weaviate at %s:%d", host, port)

            client = weaviate.connect_to_local(
                host=host,
                port=port,
            )
            
            logger.info("Connected to Weaviate successfully")
            return client

    def clear_index(self) -> None:
        """
        Clear all documents from index.
        
        WARNING: This deletes all data!
        """
        logger.warning("Clearing index - all documents will be deleted!")
        
        self.schema_manager._delete_schema()
        self.schema_manager._create_schema()
        
        logger.info("Index cleared successfully")

    def get_stats(self):
        """Get index statistics."""
        return self.schema_manager.get_stats()