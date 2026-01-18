from __future__ import annotations

import logging

from fastapi import FastAPI

from .routers.crewai import router as crew_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for CrewAI service
app = FastAPI(
    title="Research-Assistant-CrewAI-Service",
    description="Agentic workflow service using CrewAI for multi-agent orchestration.",
    version="0.1.0",
)

app.include_router(crew_router)