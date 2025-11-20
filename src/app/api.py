from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..rag.service import RAGService

router = APIRouter()
rag_service = RAGService()


class SummaryRequest(BaseModel):
    topic: str
    max_sentences: Optional[int] = 8


class SummaryResponse(BaseModel):
    answer: str


@router.post("/summarize", response_model=SummaryResponse)
async def summarize(req: SummaryRequest) -> SummaryResponse:
    """
    Core endpoint: given a topic, return a short literature-style summary.

    Later this will be fed by the multi-agent pipeline + RAG.
    For now it uses the Phase-0 RAGService wrapper.
    """
    answer = rag_service.generate_summary(
        topic=req.topic,
        max_sentences=req.max_sentences,
    )
    return SummaryResponse(answer=answer)
