"""
Main API Gateway Server
FastAPI application serving as the primary entry point for all services.
"""
from __future__ import annotations

from fastapi import FastAPI

from ..utils.logging import setup_logging
from .openapi import openapi_tags

from .routers.system import router as system_router
from .routers.crewai import router as crewai_router
from .routers.ollama import router as ollama_router
from .routers.eval import router as eval_router
from .routers.rag import router as rag_router

setup_logging(level="INFO", service_name="api-gateway")

app = FastAPI(
    title="Research-Assistant-API-Gateway",
    description="Research assistant that creates short literature summaries with references.",
    version="0.2.0",
    openapi_tags=openapi_tags(),
)

app.include_router(system_router)
app.include_router(crewai_router)
app.include_router(ollama_router)
app.include_router(eval_router)
app.include_router(rag_router)