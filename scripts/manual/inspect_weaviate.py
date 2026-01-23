#!/usr/bin/env python3
"""
Inspect Weaviate database contents.
Useful for debugging and data exploration.

Usage:
    python scripts/manual/inspect_weaviate.py [command]

Commands:
    collections     - List all collections
    schema          - Show schema details
    count           - Count documents
    sample          - Show sample documents
    search <query>  - Search documents
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import weaviate
from weaviate.classes.init import Auth
from tabulate import tabulate


WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")


def connect_weaviate():
    """Connect to Weaviate."""
    print(f"Connecting to Weaviate at {WEAVIATE_URL}...")
    
    # Parse URL
    from urllib.parse import urlparse
    parsed = urlparse(WEAVIATE_URL if WEAVIATE_URL.startswith('http') else f'http://{WEAVIATE_URL}')
    host = parsed.hostname or 'localhost'
    port = parsed.port or 8080
    
    client = weaviate.connect_to_local(host=host, port=port)
    print("✅ Connected")
    return client


def list_collections(client):
    """List all collections."""
    print("\n" + "=" * 60)
    print("COLLECTIONS")
    print("=" * 60)
    
    collections = client.collections.list_all()
    
    if not collections:
        print("No collections found")
        return
    
    for name, config in collections.items():
        print(f"\n📁 {name}")
        print(f"   Properties: {len(config.properties)}")


def show_schema(client):
    """Show detailed schema."""
    print("\n" + "=" * 60)
    print("SCHEMA DETAILS")
    print("=" * 60)
    
    collections = client.collections.list_all()
    
    for name, config in collections.items():
        print(f"\n📁 Collection: {name}")
        print(f"   Vectorizer: {config.vectorizer or 'none'}")
        
        print(f"\n   Properties:")
        for prop in config.properties:
            print(f"     - {prop.name} ({prop.data_type})")


def count_documents(client):
    """Count documents in each collection."""
    print("\n" + "=" * 60)
    print("DOCUMENT COUNTS")
    print("=" * 60)
    
    collections = client.collections.list_all()
    
    data = []
    for name in collections.keys():
        collection = client.collections.get(name)
        count = len(collection)
        data.append([name, count])
    
    print("\n" + tabulate(data, headers=["Collection", "Count"], tablefmt="grid"))


def show_sample(client, limit=5):
    """Show sample documents."""
    print("\n" + "=" * 60)
    print(f"SAMPLE DOCUMENTS (limit={limit})")
    print("=" * 60)
    
    collection_name = "ResearchDocument"
    
    try:
        collection = client.collections.get(collection_name)
        
        # Query for sample
        response = collection.query.fetch_objects(limit=limit)
        
        if not response.objects:
            print(f"\nNo documents in {collection_name}")
            return
        
        for i, obj in enumerate(response.objects, 1):
            print(f"\n--- Document {i} ---")
            print(f"UUID: {obj.uuid}")
            
            props = obj.properties
            print(f"Source: {props.get('source', 'N/A')}")
            print(f"Chunk Index: {props.get('chunk_index', 'N/A')}")
            
            content = props.get('content', '')
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"Content: {preview}")
            
    except Exception as e:
        print(f"Error: {e}")


def search_documents(client, query, limit=5):
    """Search documents."""
    print("\n" + "=" * 60)
    print(f"SEARCH RESULTS: '{query}'")
    print("=" * 60)
    
    collection_name = "ResearchDocument"
    
    try:
        collection = client.collections.get(collection_name)
        
        # BM25 search
        response = collection.query.bm25(
            query=query,
            limit=limit
        )
        
        if not response.objects:
            print(f"\nNo results found")
            return
        
        for i, obj in enumerate(response.objects, 1):
            props = obj.properties
            
            print(f"\n--- Result {i} ---")
            print(f"Score: {obj.metadata.score if hasattr(obj.metadata, 'score') else 'N/A'}")
            print(f"Source: {props.get('source', 'N/A')}")
            
            content = props.get('content', '')
            preview = content[:300] + "..." if len(content) > 300 else content
            print(f"Content: {preview}")
            
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point."""
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if command == "help":
        print(__doc__)
        return
    
    client = None
    try:
        client = connect_weaviate()
        
        if command == "collections":
            list_collections(client)
        
        elif command == "schema":
            show_schema(client)
        
        elif command == "count":
            count_documents(client)
        
        elif command == "sample":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            show_sample(client, limit)
        
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: inspect_weaviate.py search <query>")
                sys.exit(1)
            query = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            search_documents(client, query, limit)
        
        else:
            print(f"Unknown command: {command}")
            print("Run with 'help' for usage")
            sys.exit(1)
    
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()