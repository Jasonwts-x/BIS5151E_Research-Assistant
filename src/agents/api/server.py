"""
CrewAI Service Server
Main FastAPI application for CrewAI multi-agent workflows.
"""
from __future__ import annotations

from fastapi import FastAPI

from ...utils.logging import setup_logging
from .routers.crewai import router as crew_router

setup_logging(level="INFO", service_name="crewai-service")

# Initialize FastAPI app for CrewAI service
app = FastAPI(
    title="Research-Assistant-CrewAI-Service",
    description="Agentic workflow service using CrewAI for multi-agent orchestration.",
    version="0.2.0",
)

app.include_router(crew_router)