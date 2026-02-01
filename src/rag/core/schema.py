"""
Weaviate Schema Management.

Explicit schema definition for ResearchDocument collection.
Ensures deterministic structure and prevents schema drift.

The schema includes:
    - Core fields: content, source, chunk metadata
    - ArXiv enrichment: authors, publication_date, abstract, categories
    - Ingestion metadata: timestamp, schema_version
"""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Schema version for tracking changes
SCHEMA_VERSION = "1.0.0"

# Explicit Weaviate schema definition
RESEARCH_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "class": "ResearchDocument",
    "description": "Academic research documents chunked for RAG retrieval",
    "vectorizer": "none",  # We handle embeddings ourselves
    "properties": [
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Text content of the document chunk",
            "indexFilterable": True,
            "indexSearchable": True,
        },
        {
            "name": "source",
            "dataType": ["text"],
            "description": "Source filename or identifier",
            "indexFilterable": True,
            "indexSearchable": True,
        },
        {
            "name": "document_id",
            "dataType": ["text"],
            "description": "Unique identifier for the parent document",
            "indexFilterable": True,
        },
        {
            "name": "chunk_index",
            "dataType": ["int"],
            "description": "Sequential index of this chunk within the document",
            "indexFilterable": True,
        },
        {
            "name": "chunk_hash",
            "dataType": ["text"],
            "description": "Content hash for deduplication (SHA-256)",
            "indexFilterable": True,
        },
        {
            "name": "total_chunks",
            "dataType": ["int"],
            "description": "Total number of chunks in the parent document",
            "indexFilterable": True,
        },
        # Metadata fields (ArXiv enrichment)
        {
            "name": "authors",
            "dataType": ["text[]"],
            "description": "Document authors (if available)",
            "indexFilterable": True,
        },
        {
            "name": "publication_date",
            "dataType": ["text"],
            "description": "Publication date (ISO format)",
            "indexFilterable": True,
        },
        {
            "name": "arxiv_id",
            "dataType": ["text"],
            "description": "ArXiv paper ID (if from ArXiv)",
            "indexFilterable": True,
        },
        {
            "name": "arxiv_category",
            "dataType": ["text"],
            "description": "ArXiv primary category",
            "indexFilterable": True,
        },
        {
            "name": "abstract",
            "dataType": ["text"],
            "description": "Paper abstract (if available)",
            "indexSearchable": True,
        },
        # Ingestion metadata
        {
            "name": "ingestion_timestamp",
            "dataType": ["text"],
            "description": "When this chunk was ingested (ISO format)",
            "indexFilterable": True,
        },
        {
            "name": "schema_version",
            "dataType": ["text"],
            "description": "Schema version used during ingestion",
            "indexFilterable": True,
        },
    ],
}


class SchemaManager:
    """
    Manages Weaviate schema lifecycle.
    
    Responsibilities:
        - Create schema if missing
        - Validate schema matches expected definition
        - Handle schema mismatches (fail hard or reset)
    
    Attributes:
        client: Weaviate client instance
        allow_reset: If True, auto-reset schema on mismatch (dev mode only)
        collection_name: Name of the Weaviate collection
    """

    def __init__(self, client, allow_reset: bool = False):
        """
        Initialize schema manager.
        
        Args:
            client: Weaviate client instance
            allow_reset: If True, auto-reset schema on mismatch (dev mode)
        """
        self.client = client
        self.allow_reset = allow_reset
        self.collection_name = RESEARCH_DOCUMENT_SCHEMA["class"]

    def ensure_schema(self) -> None:
        """
        Ensure schema exists and matches expected definition.
        
        Behavior:
            - If schema missing: Create it
            - If schema matches: Continue
            - If schema mismatches:
                - allow_reset=True: Delete and recreate
                - allow_reset=False: Raise SchemaValidationError with instructions
        """
        if not self._schema_exists():
            logger.info("Schema does not exist - creating new schema")
            self._create_schema()
            logger.info("✓ Schema created successfully")
            return

        if self._schema_matches():
            logger.info("✓ Schema validation passed (version %s)", SCHEMA_VERSION)
            return

        # Schema mismatch detected
        logger.warning("⚠️  Schema mismatch detected!")

        if self.allow_reset:
            logger.warning("ALLOW_SCHEMA_RESET=true - Resetting index (data will be lost)")
            self._delete_schema()
            self._create_schema()
            logger.info("✓ Schema reset complete - you must re-ingest documents")
        else:
            raise SchemaValidationError(
                f"Schema mismatch detected for collection '{self.collection_name}'!\n\n"
                f"Expected schema version: {SCHEMA_VERSION}\n"
                f"Current schema differs from expected definition.\n\n"
                f"Options to fix:\n"
                f"1. Reset via Docker: docker compose down -v && docker compose up\n"
                f"2. Reset via CLI: python -m src.rag.cli reset-index\n"
                f"3. Reset via API: DELETE /rag/admin/reset-index\n"
                f"4. Enable auto-reset: Set ALLOW_SCHEMA_RESET=true in .env (dev only)\n\n"
                f"⚠️  Warning: Resetting will delete all indexed documents!"
            )

    def _schema_exists(self) -> bool:
        """
        Check if collection exists in Weaviate.
        
        Returns:
            True if collection exists, False otherwise
        """
        try:
            return self.client.collections.exists(self.collection_name)
        except Exception as e:
            logger.error("Failed to check schema existence: %s", e)
            return False

    def _schema_matches(self) -> bool:
        """
        Check if current schema matches expected definition.
        
        Validates that all expected properties exist in the collection.
        
        Returns:
            True if schema matches, False otherwise
        """
        try:
            collection = self.client.collections.get(self.collection_name)
            config = collection.config.get()

            # Get current property names
            current_props = {prop.name for prop in config.properties}

            # Get expected property names
            expected_props = {
                prop["name"] for prop in RESEARCH_DOCUMENT_SCHEMA["properties"]
            }

            # Check if all expected properties exist
            missing = expected_props - current_props
            extra = current_props - expected_props

            if missing or extra:
                logger.warning("Schema mismatch:")
                if missing:
                    logger.warning("  Missing properties: %s", missing)
                if extra:
                    logger.warning("  Extra properties: %s", extra)
                return False

            return True

        except Exception as e:
            logger.error("Failed to validate schema: %s", e)
            return False

    def _create_schema(self) -> None:
        """
        Create collection with explicit schema.
        
        Converts our schema dict to Weaviate's native format and creates the collection.
        """
        try:
            from weaviate.classes.config import Configure, Property, DataType

            # Convert our schema dict to Weaviate's format
            properties = []
            for prop in RESEARCH_DOCUMENT_SCHEMA["properties"]:
                # Map our dataType strings to Weaviate's DataType enum
                data_type_str = prop["dataType"][0]

                # Handle array types (e.g., "text[]")
                if data_type_str.endswith("[]"):
                    base_type = data_type_str[:-2]
                    data_type = getattr(DataType, base_type.upper() + "_ARRAY")
                else:
                    data_type = getattr(DataType, data_type_str.upper())

                properties.append(
                    Property(
                        name=prop["name"],
                        data_type=data_type,
                        description=prop.get("description"),
                        index_filterable=prop.get("indexFilterable", False),
                        index_searchable=prop.get("indexSearchable", False),
                    )
                )

            # Create collection
            self.client.collections.create(
                name=self.collection_name,
                description=RESEARCH_DOCUMENT_SCHEMA["description"],
                properties=properties,
            )

            logger.info("✓ Created collection '%s'", self.collection_name)

        except Exception as e:
            logger.error("Failed to create schema: %s", e)
            raise

    def _delete_schema(self) -> None:
        """
        Delete collection (and all its data).
        
        WARNING: This is destructive and cannot be undone!
        """
        try:
            self.client.collections.delete(self.collection_name)
            logger.info("✓ Deleted collection '%s'", self.collection_name)
        except Exception as e:
            logger.error("Failed to delete schema: %s", e)
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dictionary with document count, schema version, existence status, etc.
        """
        try:
            collection = self.client.collections.get(self.collection_name)

            # Count documents
            result = collection.aggregate.over_all(total_count=True)
            doc_count = result.total_count

            return {
                "collection_name": self.collection_name,
                "schema_version": SCHEMA_VERSION,
                "document_count": doc_count,
                "exists": True,
            }
        except Exception as e:
            logger.error("Failed to get stats: %s", e)
            return {
                "collection_name": self.collection_name,
                "exists": False,
                "error": str(e),
            }


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass