"""
CrewAI Service Server.

Main FastAPI application for CrewAI multi-agent workflows.

Architecture:
    Separate service from main API gateway (microservices pattern).
    Runs on port 8100, exposes /health, /run, /run/async, /status endpoints.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from ...utils.logging import setup_logging
from .routers import crewai

setup_logging(level="INFO", service_name="crewai-service")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research-Assistant-CrewAI-Service",
    description="Agentic workflow service using CrewAI for multi-agent orchestration.",
    version="0.1.0",
)

app.include_router(crewai.router)
logger.info("✓ Crew router registered")

logger.info("=" * 70)
logger.info("CrewAI Service initialized successfully")
logger.info("Agents: Writer, Reviewer, FactChecker, Translator")
logger.info("Endpoints: /health, /run, /run/async, /status/{job_id}")
logger.info("=" * 70)