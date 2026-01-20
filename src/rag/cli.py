#!/usr/bin/env python3
"""
RAG CLI Tool

Command-line interface for RAG administration and testing.

Usage:
    python -m src.rag.cli --help
    python -m src.rag.cli ingest-local
    python -m src.rag.cli ingest-local --pattern "arxiv*"
    python -m src.rag.cli ingest-arxiv "machine learning" --max-results 5
    python -m src.rag.cli query "What is digital transformation?"
    python -m src.rag.cli stats
    python -m src.rag.cli reset-index
    python -m src.rag.cli verify-determinism
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.rag.core import RAGPipeline
from src.rag.ingestion import IngestionEngine
from src.rag.sources import ArXivSource, LocalFileSource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_ingest_local(args):
    """Ingest documents from local filesystem."""
    print("=" * 70)
    print("INGEST FROM LOCAL FILES")
    print("=" * 70)
    print()
    
    data_dir = ROOT / "data" / "raw"
    pattern = args.pattern
    
    print(f"Data directory: {data_dir}")
    print(f"Pattern: {pattern}")
    print()
    
    # Count files
    pdfs = list(data_dir.glob(f"{pattern}.pdf"))
    txts = list(data_dir.glob(f"{pattern}.txt"))
    total = len(pdfs) + len(txts)
    
    if total == 0:
        print(f"❌ No files found matching pattern '{pattern}'")
        return 1
    
    print(f"Found {total} files:")
    for f in sorted(pdfs + txts):
        print(f"  - {f.name}")
    print()
    
    # Ingest
    engine = None
    try:
        print("Ingesting...")
        engine = IngestionEngine()
        source = LocalFileSource(data_dir)
        result = engine.ingest_from_source(source, pattern=pattern)
        
        print()
        print("=" * 70)
        print("INGESTION COMPLETE")
        print("=" * 70)
        print(f"Documents loaded: {result.documents_loaded}")
        print(f"Chunks created: {result.chunks_created}")
        print(f"Chunks ingested: {result.chunks_ingested}")
        print(f"Chunks skipped (duplicates): {result.chunks_skipped}")
        
        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for err in result.errors:
                print(f"  - {err}")
        
        return 0
        
    finally:
        if engine is not None and hasattr(engine, 'client'):
            try:
                engine.client.close()
            except Exception:
                pass


def cmd_ingest_arxiv(args):
    """Fetch and ingest papers from ArXiv."""
    print("=" * 70)
    print("INGEST FROM ARXIV")
    print("=" * 70)
    print()
    
    query = args.query
    max_results = args.max_results
    
    print(f"Query: {query}")
    print(f"Max results: {max_results}")
    print()
    
    # Ingest
    engine = None
    try:
        print("Fetching from ArXiv (this may take a minute)...")
        engine = IngestionEngine()
        source = ArXivSource(download_dir=ROOT / "data" / "raw")
        result = engine.ingest_from_source(
            source,
            query=query,
            max_results=max_results,
        )
        
        print()
        print("=" * 70)
        print("INGESTION COMPLETE")
        print("=" * 70)
        print(f"Papers fetched: {result.documents_loaded}")
        print(f"Chunks created: {result.chunks_created}")
        print(f"Chunks ingested: {result.chunks_ingested}")
        print(f"Chunks skipped (duplicates): {result.chunks_skipped}")
        
        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for err in result.errors:
                print(f"  - {err}")
        
        return 0
        
    except Exception as e:
        print(f"❌ ArXiv ingestion failed: {e}")
        logger.exception("ArXiv ingestion failed")
        return 1
        
    finally:
        # Properly close the Weaviate client
        if engine is not None and hasattr(engine, 'client'):
            try:
                engine.client.close()
            except Exception:
                pass


def cmd_query(args):
    """Test retrieval for a query."""
    print("=" * 70)
    print("QUERY TEST")
    print("=" * 70)
    print()
    
    query = args.query
    top_k = args.top_k
    
    print(f"Query: {query}")
    print(f"Top-k: {top_k}")
    print()
    
    # Connect to existing pipeline
    pipeline = None
    try:
        print("Connecting to RAG pipeline...")
        pipeline = RAGPipeline.from_existing()
        
        # Retrieve
        print(f"Retrieving top {top_k} documents...")
        docs = pipeline.run(query=query, top_k=top_k)
        
        print()
        print("=" * 70)
        print(f"RETRIEVED {len(docs)} DOCUMENTS")
        print("=" * 70)
        print()
        
        if not docs:
            print("⚠️  No documents found. Is the index empty?")
            print("   Try: python -m src.rag.cli ingest-local")
            return 0
        
        for i, doc in enumerate(docs, 1):
            meta = doc.meta or {}
            source = meta.get("source", "unknown")
            chunk_idx = meta.get("chunk_index", "?")
            
            print(f"[{i}] {source} (chunk {chunk_idx})")
            print("-" * 70)
            content_preview = doc.content[:200].replace("\n", " ")
            print(f"{content_preview}...")
            print()
        
        return 0
        
    except RuntimeError as e:
        # Collection doesn't exist
        print(f"❌ {e}")
        return 1
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        logger.exception("Query failed")
        return 1
        
    finally:
        # Properly close the pipeline client
        if pipeline is not None and hasattr(pipeline, 'client'):
            try:
                pipeline.client.close()
            except Exception:
                pass


def cmd_stats(args):
    """Show index statistics."""
    print("=" * 70)
    print("RAG INDEX STATISTICS")
    print("=" * 70)
    print()
    
    try:
        engine = IngestionEngine()
        stats = engine.get_stats()
        
        print(f"Collection: {stats['collection_name']}")
        print(f"Schema version: {stats['schema_version']}")
        print(f"Document count: {stats['document_count']}")
        print(f"Exists: {stats['exists']}")
        
        if stats.get('error'):
            print(f"Error: {stats['error']}")

        return 0
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        return 1
    
    finally:
        # Properly close the Weaviate client
        if engine is not None and hasattr(engine, 'client'):
            try:
                engine.client.close()
            except Exception:
                pass  # Ignore errors during cleanup


def cmd_reset_index(args):
    """Clear all documents from index."""
    print("=" * 70)
    print("RESET INDEX")
    print("=" * 70)
    print()
    print("⚠️  WARNING: This will DELETE ALL indexed documents!")
    print()
    
    if not args.yes:
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return 0
    
    engine = None
    try:
        engine = IngestionEngine()
        
        # Get current count
        stats = engine.get_stats()
        previous_count = stats.get("document_count", 0)
        
        print(f"Deleting {previous_count} documents...")
        
        # Reset
        engine.clear_index()
        
        print()
        print("✅ Index reset complete")
        print(f"   {previous_count} documents deleted")
        print()
        print("Re-ingest documents with:")
        print("  python -m src.rag.cli ingest-local")
        print("  python -m src.rag.cli ingest-arxiv <query>")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to reset index: {e}")
        logger.exception("Reset index failed")
        return 1
        
    finally:
        # Properly close the Weaviate client
        if engine is not None and hasattr(engine, 'client'):
            try:
                engine.client.close()
            except Exception:
                pass 

def cmd_verify_determinism(args):
    """Verify that index rebuild produces identical IDs."""
    print("=" * 70)
    print("VERIFY DETERMINISM")
    print("=" * 70)
    print()
    
    print("This test verifies that rebuilding the index produces identical chunk IDs.")
    print()
    
    # TODO: Implement determinism test
    # 1. Get current document IDs from Weaviate
    # 2. Reset index
    # 3. Re-ingest same documents
    # 4. Get new document IDs
    # 5. Compare
    
    print("⚠️  Not implemented yet - coming in testing phase")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RAG CLI - Administration and testing tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # ingest-local
    p_local = subparsers.add_parser(
        "ingest-local",
        help="Ingest documents from local filesystem (data/raw/)",
    )
    p_local.add_argument(
        "--pattern",
        type=str,
        default="*",
        help="File pattern to match (default: all files)",
    )
    
    # ingest-arxiv
    p_arxiv = subparsers.add_parser(
        "ingest-arxiv",
        help="Fetch and ingest papers from ArXiv",
    )
    p_arxiv.add_argument(
        "query",
        type=str,
        help="ArXiv search query",
    )
    p_arxiv.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of papers to fetch (default: 5)",
    )
    
    # query
    p_query = subparsers.add_parser(
        "query",
        help="Test retrieval for a query",
    )
    p_query.add_argument(
        "query",
        type=str,
        help="Search query",
    )
    p_query.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results (default: 5)",
    )
    
    # stats
    subparsers.add_parser(
        "stats",
        help="Show index statistics",
    )
    
    # reset-index
    p_reset = subparsers.add_parser(
        "reset-index",
        help="Clear all documents from index (DESTRUCTIVE)",
    )
    p_reset.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    
    # verify-determinism
    subparsers.add_parser(
        "verify-determinism",
        help="Verify that rebuild produces identical IDs",
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command
    commands = {
        "ingest-local": cmd_ingest_local,
        "ingest-arxiv": cmd_ingest_arxiv,
        "query": cmd_query,
        "stats": cmd_stats,
        "reset-index": cmd_reset_index,
        "verify-determinism": cmd_verify_determinism,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())