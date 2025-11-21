from __future__ import annotations

import logging

from fastapi import FastAPI

from .api import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


app = FastAPI(
    title="ResearchAssistantGPT",
    description="Research assistant that creates short literature summaries with references.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")

# Run with:
#   uvicorn src.app.server:app --reload --host 0.0.0.0 --port 8000
