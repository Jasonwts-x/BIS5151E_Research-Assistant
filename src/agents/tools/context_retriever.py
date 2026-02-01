"""
Context Retrieval Tool.

Allows agents to dynamically retrieve additional context from the RAG knowledge base.
Enables agents to search for specific information when initial context is insufficient.

Architecture:
    Integrates with RAG pipeline to provide on-demand document retrieval.
    Returns formatted documents with citation numbers for easy reference.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from crewai.tools import tool

logger = logging.getLogger(__name__)


@tool
def retrieve_context(query: str, top_k: int = 3) -> Dict[str, any]:
    """
    Retrieve additional context from the RAG knowledge base.
    
    Args:
        query: Search query
        top_k: Number of documents to retrieve (max: 5)
        
    Returns:
        Dictionary with documents, count, and status message
    """
    try:
        # Import here to avoid circular imports
        from ...rag.core import RAGPipeline
        
        # Validate top_k parameter
        top_k = min(max(1, top_k), 5)
        
        logger.info("Context retrieval tool invoked: query='%s', top_k=%d", query, top_k)
        
        # Execute RAG retrieval
        pipeline = RAGPipeline.from_existing()
        docs = pipeline.run(query=query, top_k=top_k)
        
        # Format documents for agent consumption
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            # Truncate content to 500 chars to avoid overwhelming the agent
            content = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
            
            formatted_docs.append({
                "citation_number": i,
                "source": doc.meta.get("source", "unknown"),
                "content": content,
                "metadata": {
                    "title": doc.meta.get("title", ""),
                    "authors": doc.meta.get("authors", ""),
                    "year": doc.meta.get("year", ""),
                }
            })
        
        logger.info("Successfully retrieved %d documents via context retrieval tool", len(docs))
        
        return {
            "success": True,
            "documents": formatted_docs,
            "count": len(docs),
            "query": query,
            "message": f"Successfully retrieved {len(docs)} documents. Use citation numbers [1], [2], etc. to cite sources.",
        }
        
    except Exception as e:
        logger.error("Context retrieval tool failed: %s", e)
        return {
            "success": False,
            "documents": [],
            "count": 0,
            "query": query,
            "message": f"Context retrieval failed: {str(e)}. Use only the initially provided context.",
        }