from __future__ import annotations

import logging
import os
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ...rag.service import RAGService
from ..dependencies import get_rag_service
from ..errors import internal_server_error
from ..openapi import APITag
from ..schemas.rag import RAGQueryRequest, RAGQueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=[APITag.RAG])

# CrewAI service URL (internal Docker network)
CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Run RAG + generation and return a final answer.",
)
async def rag_query(
    payload: RAGQueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
) -> RAGQueryResponse:
    """
    Execute full RAG pipeline with multi-agent processing.
    
    This endpoint:
    1. Retrieves relevant context using RAG (Weaviate + hybrid search)
    2. Forwards the query to the CrewAI service for agent processing
    3. Returns the final fact-checked summary
    
    The CrewAI service handles:
    - Writer agent: Drafts initial summary
    - Reviewer agent: Improves clarity and coherence
    - FactChecker agent: Verifies claims and citations
    - (Future: Translator agent for non-English output)
    
    Note: This is the recommended user-facing endpoint for research queries.
    For more control, you can call /crewai/run directly and manage RAG retrieval yourself.
    """
    try:
        logger.info(
            "RAG query request: topic='%s', language='%s'",
            payload.query,
            payload.language,
        )
        
        # Forward to CrewAI service (which handles RAG retrieval internally)
        # The CrewAI service will retrieve context and run the agent pipeline
        async with httpx.AsyncClient(timeout=120.0) as client:  # Long timeout for LLM
            response = await client.post(
                f"{CREWAI_URL}/crew/run",
                json={
                    "topic": payload.query,
                    "language": payload.language,
                },
            )
            response.raise_for_status()
            
            crew_result = response.json()
            
            logger.info("CrewAI service completed successfully")
            
            return RAGQueryResponse(
                query=payload.query,
                language=payload.language,
                answer=crew_result["answer"],
                timings={},  # TODO: Get timings from crew service if needed
            )
            
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"CrewAI service error: {e.response.text}",
        ) from e
        
    except httpx.RequestError as e:
        logger.error("Failed to reach CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e
        
    except Exception as err:
        logger.exception("RAG query failed internally.")
        raise internal_server_error(
            "An error occurred while processing the request."
        ) from err


# ---------------------------------------------------------------------------
# Future endpoints (intentionally NOT implemented yet)
# ---------------------------------------------------------------------------
# 1) POST /rag/ingest
#    - Add once we decide deterministic ingestion + stable IDs (Step E).
#
# 2) GET /rag/retrieve
#    - Add if we want a RAG-only endpoint (retrieval without agents)
#    - Useful for debugging or building custom workflows