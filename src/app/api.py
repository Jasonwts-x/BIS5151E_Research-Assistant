from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..agents.factchecker import default_factchecker
from ..agents.orchestrator import serialize_result
from ..agents.reviewer import default_reviewer
from ..agents.translator import default_translator
from ..agents.writer import default_writer
from ..rag.service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# Shared agent instances (singletons for whole FastAPI process)
#   - Direct endpoints still use them (writer / reviewer / factchecker / translator)
#   - The full pipeline now goes through RAGService, which internally uses
#     its own default_orchestrator().
# ---------------------------------------------------------------------------

WRITER = default_writer()
REVIEWER = default_reviewer()
FACTCHECKER = default_factchecker()
TRANSLATOR = default_translator()

# High-level RAG + multi-agent service
RAG_SERVICE = RAGService()


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class WriterRequest(BaseModel):
    topic: str = Field(..., description="Topic or research question.")
    context: Optional[str] = Field(
        None,
        description="Optional external context (e.g. from RAG or another system).",
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
    # NOTE: kept for forward-compatibility with n8n etc.
    #       For now, the server builds its own RAG context internally.
    context: Optional[str] = Field(
        None,
        description=(
            "Optional additional context. The server will still perform RAG "
            "internally; this field can be used later to append custom context."
        ),
    )


class PipelineResponse(BaseModel):
    topic: str
    language: str
    writer_output: str
    reviewed_output: str
    checked_output: str
    final_output: str


# ---------------------------------------------------------------------------
# Agent Endpoints
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Pipeline Endpoint (now via RAGService)
# ---------------------------------------------------------------------------


@router.post(
    "/pipeline/summary",
    response_model=PipelineResponse,
    summary="Run complete Writer → Reviewer → FactChecker → (Translator) pipeline with RAG context.",
)
def run_pipeline(payload: PipelineRequest) -> PipelineResponse:
    """
    End-to-end pipeline:

    - Uses RAGService to retrieve relevant chunks from data/raw via Haystack.
    - Builds a context string with numbered sources.
    - Runs Writer → Reviewer → FactChecker → (optional) Translator.
    """
    result = RAG_SERVICE.run_with_agents(
        topic=payload.topic,
        language=payload.language,
        # In the future we might combine payload.context with the RAG context.
    )
    data = serialize_result(result)
    return PipelineResponse(**data)


# Backwards-compatible alias for earlier experiments
@router.post("/summarize", response_model=PipelineResponse)
def summarize_alias(payload: PipelineRequest) -> PipelineResponse:
    return run_pipeline(payload)
