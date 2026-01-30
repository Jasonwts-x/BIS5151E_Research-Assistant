"""
Main API Gateway Server

FastAPI application serving as the primary entry point for all services.
Routes requests to research, RAG, CrewAI, Ollama, and system endpoints.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from ..utils.logging import setup_logging
from .openapi import openapi_tags

from .routers import crewai, eval, ollama, rag, system, research

# Setup logging
setup_logging(level="INFO", service_name="api-gateway")
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Research-Assistant-API-Gateway",
    description="Research assistant that creates short fact-checked literature summaries with citations.",
    version="0.2.0",
    openapi_tags=openapi_tags(),
)

# Register routers in order of importance
logger.info("Registering API routers...")

app.include_router(system.router)
logger.info("✓ System router registered")

app.include_router(research.router)
logger.info("✓ Research router registered")

app.include_router(crewai.router)
logger.info("✓ CrewAI router registered")

app.include_router(ollama.router)
logger.info("✓ Ollama router registered")

app.include_router(eval.router)
logger.info("✓ Eval router registered")

app.include_router(rag.router)
logger.info("✓ RAG router registered")

logger.info("=" * 70)
logger.info("API Gateway initialized successfully")
logger.info("Documentation: http://localhost:8000/docs")
logger.info("  Primary endpoint: POST /research/query")
logger.info("=" * 70)