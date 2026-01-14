from __future__ import annotations

import logging

from fastapi import FastAPI

from .openapi import openapi_tags
from .routers.rag import router as rag_router
from .routers.system import router as system_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research-Assistant-API",
    description="Research assistant that creates short literature summaries with references.",
    version="0.2.0",
    openapi_tags=openapi_tags(),
)

app.include_router(system_router)
app.include_router(rag_router)
