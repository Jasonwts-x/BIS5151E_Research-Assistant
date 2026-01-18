from __future__ import annotations

import logging
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from ollama import chat, list as ollama_list

from ...utils.config import AppConfig
from ..dependencies import get_config
from ..openapi import APITag
from ..schemas.ollama import (
    OllamaChatRequest,
    OllamaChatResponse,
    OllamaInfoResponse,
    OllamaModel,
    OllamaModelsResponse,
    OllamaPullRequest,
    OllamaPullResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ollama", tags=[APITag.OLLAMA])


# ============================================================================
# Service Health & Information
# ============================================================================


@router.get(
    "/info",
    response_model=OllamaInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Ollama service information and status.",
)
def ollama_info(
    cfg: Annotated[AppConfig, Depends(get_config)],
) -> OllamaInfoResponse:
    """
    Returns Ollama service status, configured model, and list of available models.
    
    Useful for debugging and verifying Ollama connectivity.
    """
    base_url = cfg.llm.host
    configured_model = cfg.llm.model

    # Check health
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        is_healthy = resp.status_code == 200
    except Exception as e:
        logger.error("Failed to reach Ollama at %s: %s", base_url, e)
        is_healthy = False

    # Get available models
    available_models: list[str] = []
    if is_healthy:
        try:
            models_data = ollama_list()
            available_models = [
                m.get("name") or m.get("model", "") 
                for m in models_data.get("models", [])
            ]
        except Exception as e:
            logger.warning("Failed to list Ollama models: %s", e)

    return OllamaInfoResponse(
        status="healthy" if is_healthy else "unhealthy",
        host=base_url,
        configured_model=configured_model,
        available_models=available_models,
    )


@router.get(
    "/models",
    response_model=OllamaModelsResponse,
    status_code=status.HTTP_200_OK,
    summary="List all available Ollama models.",
)
def list_models() -> OllamaModelsResponse:
    """
    Returns detailed information about all models available in Ollama.
    
    Equivalent to running `ollama list` in the CLI.
    """
    try:
        data = ollama_list()
        models = [
            OllamaModel(
                name=m.get("name") or m.get("model", ""),
                size=m.get("size"),
                digest=m.get("digest"),
                modified_at=m.get("modified_at"),
                details=m.get("details", {}),
            )
            for m in data.get("models", [])
        ]
        return OllamaModelsResponse(models=models)
    except Exception as e:
        logger.error("Failed to list Ollama models: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not retrieve models from Ollama: {str(e)}",
        ) from e


# ============================================================================
# Chat Completion (Placeholder for Step D)
# ============================================================================


@router.post(
    "/chat",
    response_model=OllamaChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat completion via Ollama (direct LLM access).",
)
def chat_completion(
    payload: OllamaChatRequest,
    cfg: Annotated[AppConfig, Depends(get_config)],
) -> OllamaChatResponse:
    """
    Direct chat completion endpoint using Ollama.
    
    **Note**: This is a low-level endpoint for testing/debugging.
    For production use, prefer the `/rag/query` endpoint which includes
    retrieval-augmented generation and multi-agent processing.
    
    TODO (Step D - CrewAI Integration):
    - Add streaming support
    - Integrate with CrewAI tool calling if needed
    """
    model = payload.model or cfg.llm.model

    try:
        messages = [{"role": m.role, "content": m.content} for m in payload.messages]
        
        options = {}
        if payload.temperature is not None:
            options["temperature"] = payload.temperature

        response = chat(
            model=model,
            messages=messages,
            stream=payload.stream,
            options=options or None,
        )

        return OllamaChatResponse(
            model=model,
            message={
                "role": "assistant",
                "content": response.message.content,
            },
            done=True,
        )
    except Exception as e:
        logger.error("Chat completion failed with model %s: %s", model, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}",
        ) from e


# ============================================================================
# Model Management (Placeholder for Step G - QoL)
# ============================================================================


@router.post(
    "/pull",
    response_model=OllamaPullResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Pull/download a model (not implemented yet).",
)
def pull_model(payload: OllamaPullRequest) -> OllamaPullResponse:
    """
    Trigger download of a new model.
    
    TODO (Step G - QoL):
    - Implement actual model pulling
    - Consider making this async (long-running operation)
    - Add progress tracking endpoint
    - Add webhook/callback when complete
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Model pulling not implemented yet. Use `docker compose exec ollama ollama pull <model>` for now.",
    )


# ============================================================================
# TODO: Implement in Step D (CrewAI Integration)
# - Add streaming support for /chat endpoint
# - Add tool/function calling support if needed by CrewAI agents
# - Consider adding a /generate endpoint for non-chat use cases
# ============================================================================

# ============================================================================
# TODO: Implement in Step G (QoL)
# - POST /ollama/delete - remove a model
# - GET /ollama/show/:model - detailed model info
# - POST /ollama/copy - copy/rename a model
# - POST /ollama/embeddings - generate embeddings (if not using sentence-transformers)
# ============================================================================