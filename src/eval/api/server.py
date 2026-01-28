"""
Evaluation Service Server
Main FastAPI application for evaluation service.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ...utils.logging import setup_logging
from .routers import health, metrics

# Configure logging once for the entire service
setup_logging(level="INFO", service_name="eval-service")
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ResearchAssistant-Evaluation-Service",
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
logger.info("✓ Health router registered")

app.include_router(metrics.router)
logger.info("✓ Metrics router registered")

logger.info("=" * 70)
logger.info("Evaluation Service initialized successfully")
logger.info("Endpoints: /health, /metrics/*")
logger.info("=" * 70)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "ResearchAssistant Evaluation Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
        },
    }