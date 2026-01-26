"""
Evaluation Service Server
Main FastAPI application for evaluation service.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ResearchAssistant Evaluation Service",
    description="Evaluation and monitoring API for ResearchAssistantGPT",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(metrics.router)

logger.info("Evaluation Service API initialized")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "ResearchAssistant Evaluation Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "dashboard": "http://localhost:8501",
        },
    }