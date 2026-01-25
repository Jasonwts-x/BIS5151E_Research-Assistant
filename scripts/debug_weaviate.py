#!/usr/bin/env python3
"""
Debug script to inspect Weaviate collection and test retrieval.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import load_config


def main():
    print("=" * 70)
    print("WEAVIATE DEBUG SCRIPT")
    print("=" * 70)
    print()
    
    # Load config
    cfg = load_config()
    
    # Import here to use config
    import weaviate
    
    # Connect to Weaviate using config
    print(f"Connecting to Weaviate at {cfg.weaviate.url}...")
    
    # CRITICAL: Use weaviate hostname (Docker network) not localhost
    # Parse URL to get host and port
    from urllib.parse import urlparse
    parsed = urlparse(cfg.weaviate.url if cfg.weaviate.url.startswith('http') else f'http://{cfg.weaviate.url}')
    host = parsed.hostname or 'weaviate'
    port = parsed.port or 8080
    
    print(f"Connecting to {host}:{port}...")
    client = weaviate.connect_to_local(host=host, port=port)
    
    try:
        # Check if collection exists
        collection_name = "ResearchDocument"
        
        if not client.collections.exists(collection_name):
            print(f"❌ Collection '{collection_name}' does not exist!")
            return 1
        
        print(f"✅ Collection '{collection_name}' exists")
        print()
        
        # Get collection
        collection = client.collections.get(collection_name)
        
        # Get document count
        response = collection.aggregate.over_all(total_count=True)
        count = response.total_count
        
        print(f"📊 Total documents in collection: {count}")
        print()
        
        if count == 0:
            print("⚠️  Collection is empty! No documents to retrieve.")
            print("   Run ingestion first:")
            print("   POST /rag/ingest/arxiv")
            return 0
        
        # Fetch first 5 documents
        print("📄 First 5 documents:")
        print("-" * 70)
        
        results = collection.query.fetch_objects(limit=5)
        
        for i, obj in enumerate(results.objects, 1):
            props = obj.properties
            print(f"\n{i}. Document:")
            print(f"   Source: {props.get('source', 'N/A')}")
            print(f"   Chunk Index: {props.get('chunk_index', 'N/A')}")
            print(f"   Content: {props.get('content', '')[:100]}...")
        
        print()
        print("-" * 70)
        print()
        
        # Test hybrid search
        print("🔍 Testing hybrid search for 'transformer'...")
        
        from src.rag.core.pipeline import RAGPipeline
        
        pipeline = RAGPipeline.from_existing()
        docs = pipeline.run(query="transformer", top_k=3)
        
        print(f"✅ Retrieved {len(docs)} documents")
        
        for i, doc in enumerate(docs, 1):
            meta = doc.meta or {}
            print(f"\n{i}. Retrieved Document:")
            print(f"   Source: {meta.get('source', 'N/A')}")
            print(f"   Score: {doc.score if hasattr(doc, 'score') and doc.score else 'N/A'}")
            print(f"   Content: {doc.content[:150] if doc.content else '[No content]'}...")
        
        print()
        print("=" * 70)
        print("DEBUG COMPLETE")
        print("=" * 70)
        
        return 0
        
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())