"""
Main API Gateway Server
FastAPI application serving as the primary entry point for all services.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from ..utils.logging import setup_logging
from .openapi import openapi_tags
from .routers import crewai, eval, ollama, rag, system

# Configure logging once for the entire service
setup_logging(level="INFO", service_name="api-gateway")
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Research-Assistant-API-Gateway",
    description="Research assistant that creates short literature summaries with references.",
    version="0.2.0",
    openapi_tags=openapi_tags(),
)

# Include routers
app.include_router(system.router)
logger.info("✓ System router registered")

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
logger.info("=" * 70)