"""
Research Assistant Package

Root package for the ResearchAssistantGPT application.

This package provides a RAG-based research assistant with multi-agent workflows:
- Document ingestion from local files and ArXiv
- Vector-based hybrid retrieval using Weaviate
- Multi-agent summarization via CrewAI
- Orchestration through n8n workflows

Architecture:
    - src/rag: Core RAG pipeline (Haystack + Weaviate)
    - src/agents: Multi-agent system (CrewAI)
    - src/api: FastAPI gateway service
    - src/eval: Quality assurance (TruLens + Guardrails)
    - src/utils: Shared configuration and utilities
"""
from __future__ import annotations