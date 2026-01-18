from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from ...rag.service import RAGService
from ..dependencies import get_rag_service
from ..errors import internal_server_error
from ..openapi import APITag
from ..schemas.rag import RAGQueryRequest, RAGQueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=[APITag.RAG])


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Run RAG + generation and return a final answer.",
)
def rag_query(
    payload: RAGQueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
) -> RAGQueryResponse:
    try:
        result = rag.run_with_agents(topic=payload.query, language=payload.language)
    except Exception as err:
        logger.exception("RAG query failed internally.")
        raise internal_server_error(
            "An error occurred while processing the request."
        ) from err

    timings = getattr(result, "timings", {}) or {}
    answer = getattr(result, "final_output", "")

    return RAGQueryResponse(
        query=payload.query,
        language=payload.language,
        answer=answer,
        timings=timings,
    )


# ---------------------------------------------------------------------------
# Future endpoints (intentionally NOT implemented yet)
# ---------------------------------------------------------------------------
# 1) POST /rag/ingest
#    - Add once we decide deterministic ingestion + stable IDs (Step E).
#
# 2) POST /crew/run or /agent/run
#    - Add after CrewAI integration (Step D). Likely async job contract.
