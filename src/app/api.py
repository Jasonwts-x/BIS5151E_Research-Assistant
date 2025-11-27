from __future__ import annotations

import logging
from typing import Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..agents.factchecker import default_factchecker
from ..agents.orchestrator import (
    default_orchestrator,
    serialize_result,
)
from ..agents.reviewer import default_reviewer
from ..agents.translator import default_translator
from ..agents.writer import default_writer
from ..rag.service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()

# ----- Global singletons ---------------------------------------------------

# Individual agents for direct “microservice-style” calls
WRITER = default_writer()
REVIEWER = default_reviewer()
FACTCHECKER = default_factchecker()
TRANSLATOR = default_translator()

# Full orchestrator (used earlier; kept for backwards compatibility)
ORCHESTRATOR = default_orchestrator()

# RAG + multi-agent facade: one instance per process
RAG = RAGService()


# ----- Pydantic models -----------------------------------------------------


class WriterRequest(BaseModel):
    topic: str = Field(..., description="Topic or research question.")
    context: Optional[str] = Field(
        None,
        description="Optional retrieved context (e.g., from RAG).",
    )


class WriterResponse(BaseModel):
    draft: str


class ReviewerRequest(BaseModel):
    draft: str


class ReviewerResponse(BaseModel):
    reviewed: str


class FactCheckerRequest(BaseModel):
    text: str
    context: Optional[str] = None


class FactCheckerResponse(BaseModel):
    checked: str


class TranslatorRequest(BaseModel):
    text: str
    target_language: str = Field("en", examples=["en", "de", "fr"])


class TranslatorResponse(BaseModel):
    translated: str


class PipelineRequest(BaseModel):
    topic: str
    language: str = Field("en", examples=["en", "de", "fr"])
    context: Optional[str] = Field(
        None,
        description=(
            "Optional context (currently ignored by RAGService; "
            "reserved for future overrides)."
        ),
    )


class PipelineResponse(BaseModel):
    topic: str
    language: str
    writer_output: str
    reviewed_output: str
    checked_output: str
    final_output: str
    timings: Dict[str, float]


# ----- Agent endpoints -----------------------------------------------------


@router.post("/agent/writer", response_model=WriterResponse)
def call_writer(payload: WriterRequest) -> WriterResponse:
    draft = WRITER.run(topic=payload.topic, context=payload.context)
    return WriterResponse(draft=draft)


@router.post("/agent/reviewer", response_model=ReviewerResponse)
def call_reviewer(payload: ReviewerRequest) -> ReviewerResponse:
    reviewed = REVIEWER.run(draft=payload.draft)
    return ReviewerResponse(reviewed=reviewed)


@router.post("/agent/factchecker", response_model=FactCheckerResponse)
def call_factchecker(payload: FactCheckerRequest) -> FactCheckerResponse:
    checked = FACTCHECKER.run(text=payload.text, context=payload.context)
    return FactCheckerResponse(checked=checked)


@router.post("/agent/translator", response_model=TranslatorResponse)
def call_translator(payload: TranslatorRequest) -> TranslatorResponse:
    translated = TRANSLATOR.run(
        text=payload.text,
        target_language=payload.target_language,
    )
    return TranslatorResponse(translated=translated)


# ----- RAG + multi-agent pipeline endpoint --------------------------------


@router.post(
    "/pipeline/summary",
    response_model=PipelineResponse,
    summary="Run RAG + writer → reviewer → factchecker → (translator) pipeline.",
)
def run_pipeline(payload: PipelineRequest) -> PipelineResponse:
    """
    Main endpoint for the project:
    - Uses RAGService to retrieve context from data/raw
    - Runs the multi-agent orchestrator with that context
    - Returns all intermediate steps + timings
    """
    result = RAG.run_with_agents(
        topic=payload.topic,
        language=payload.language,
    )
    data = serialize_result(result)
    return PipelineResponse(**data)


# Backwards-compatible alias for earlier experiments
@router.post("/summarize", response_model=PipelineResponse)
def summarize_alias(payload: PipelineRequest) -> PipelineResponse:
    return run_pipeline(payload)
