"""
Main API Gateway.

FastAPI application serving as the primary entry point for all services.
Routes requests to RAG, Ollama, CrewAI, and system endpoints.

Architecture:
    - Gateway pattern: Single entry point proxying to microservices
    - Research service (port 8100): CrewAI multi-agent workflows
    - Ollama service (port 11434): LLM inference
    - Eval service (port 8502): Quality metrics and monitoring
    - Weaviate (port 8080): Vector database for RAG
"""
from __future__ import annotations