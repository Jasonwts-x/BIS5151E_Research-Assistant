from __future__ import annotations

import logging
import platform

import requests
from fastapi import APIRouter, status

from ...utils.config import load_config
from ..openapi import APITag
from ..schemas.system import HealthResponse, ReadyResponse, VersionResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=[APITag.SYSTEM])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check: confirms the API process is responsive.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Service, version and basic runtime info.",
)
def version() -> VersionResponse:
    return VersionResponse(
        service="research-assistant-api",
        api_version="0.2.0",
        python_version=platform.python_version(),
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check: verifies dependent services are reachable.",
)
def ready() -> ReadyResponse:
    cfg = load_config()

    weaviate_ok = _check_weaviate(cfg.weaviate.url)
    ollama_ok = _check_ollama_optional(cfg.llm.host)

    status_text = "ok" if weaviate_ok and (ollama_ok in [True, None]) else "degraded"
    return ReadyResponse(
        status=status_text,
        weaviate_ok=weaviate_ok,
        ollama_ok=ollama_ok,
    )


def _check_weaviate(base_url: str) -> bool:
    base = base_url.rstrip("/")
    try:
        r = requests.get(f"{base}/v1/.well-known/ready", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _check_ollama_optional(host: str) -> bool | None:
    """
    In Step B, Ollama is not guaranteed to exist.
    If it's not configured, we consider it 'ok' for readiness.
    We'll tighten this in Step C when Ollama becomes a real service.
    """
    base = (host or "").rstrip("/")
    if not base:
        return None

    try:
        r = requests.get(f"{base}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ============================================================================
# Aggregated Service Health Check
# ============================================================================


@router.get(
    "/health/services",
    status_code=status.HTTP_200_OK,
    summary="Check health of all downstream services",
)
def health_services():
    """
    Check health of all downstream services.
    
    Returns status for:
    - Weaviate (vector database)
    - Ollama (LLM service)
    - CrewAI (agent service)
    - Eval (evaluation service)
    
    Useful for monitoring and debugging the entire system.
    """
    import os
    
    services_status = {}
    
    # Check Weaviate
    cfg = load_config()
    services_status["weaviate"] = {
        "healthy": _check_weaviate(cfg.weaviate.url),
        "url": cfg.weaviate.url,
    }
    
    # Check Ollama
    ollama_healthy = _check_ollama_optional(cfg.llm.host)
    services_status["ollama"] = {
        "healthy": ollama_healthy if ollama_healthy is not None else False,
        "url": cfg.llm.host,
        "optional": ollama_healthy is None,
    }
    
    # Check CrewAI service
    crewai_url = os.getenv("CREWAI_URL", "http://crewai:8100")
    try:
        r = requests.get(f"{crewai_url}/health", timeout=2)
        crewai_healthy = r.status_code == 200
    except Exception:
        crewai_healthy = False
    
    services_status["crewai"] = {
        "healthy": crewai_healthy,
        "url": crewai_url,
    }
    
    # Check Eval service
    eval_url = os.getenv("EVAL_SERVICE_URL", "http://eval:8502")
    try:
        r = requests.get(f"{eval_url}/health", timeout=2)
        eval_healthy = r.status_code == 200
    except Exception:
        eval_healthy = False
    
    services_status["eval"] = {
        "healthy": eval_healthy,
        "url": eval_url,
    }
    
    # Overall status
    all_healthy = all(
        service["healthy"] 
        for service in services_status.values()
        if not service.get("optional", False)
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services_status,
    }