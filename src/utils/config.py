"""
Configuration Management

Loads and merges configuration from configs/app.yaml and environment variables.
Environment variables take precedence over YAML values.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "configs" / "app.yaml"


# ============================================================================
# Application Configuration - Data Classes
# ============================================================================

@dataclass
class LLMConfig:
    """LLM service configuration."""
    provider: str = "ollama"
    model: str = "qwen2.5:3b"
    host: str = "http://ollama:11434"


@dataclass
class AgentLLMConfig:
    """Agent-specific LLM configuration."""
    temperature: float = 0.3
    max_iterations: int = 1
    verbose: bool = True
    timeout: int = 600


@dataclass
class CrewConfig:
    """Crew execution configuration."""
    process: str = "sequential"
    memory: bool = False
    cache: bool = True


@dataclass
class AgentsConfig:
    """Agent system configuration."""
    llm: AgentLLMConfig
    crew: CrewConfig


@dataclass
class RAGConfig:
    """RAG pipeline configuration."""
    backend: str = "weaviate"
    chunk_size: int = 350
    chunk_overlap: int = 60
    top_k: int = 5
    allow_schema_reset: bool = False


@dataclass
class WeaviateConfig:
    """Weaviate vector database configuration."""
    url: str = "http://weaviate:8080"
    api_key: Optional[str] = None
    index_name: str = "research_assistant"
    text_key: str = "content"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class GuardrailsConfig:
    """Safety guardrails configuration."""
    citation_required: bool = True
    strict_mode: bool = False


@dataclass
class EvalConfig:
    """Evaluation system configuration."""
    faithfulness_metric: str = "trulens_groundedness"
    enable_trulens: bool = True
    enable_performance_tracking: bool = True


@dataclass
class AppConfig:
    """Complete application configuration."""
    llm: LLMConfig
    agents: AgentsConfig
    rag: RAGConfig
    weaviate: WeaviateConfig
    guardrails: GuardrailsConfig
    eval: EvalConfig


# ============================================================================
# Application Configuration - Functions
# ============================================================================

def _read_yaml(path: Path) -> Dict[str, Any]:
    """Read YAML configuration file."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config() -> AppConfig:
    """
    Load configuration from configs/app.yaml and environment variables.
    
    Environment variables override YAML values for maximum flexibility.
    
    Returns:
        Complete application configuration.
    """
    load_dotenv(ROOT / ".env", override=False)

    y = _read_yaml(CONFIG_FILE)
    if not y:
        print(f"ℹ️  No configs/app.yaml found at {CONFIG_FILE}, using defaults/env only.")

    llm_y = y.get("llm") or {}
    agents_y = y.get("agents") or {}
    agent_llm_y = agents_y.get("llm") or {}
    crew_y = agents_y.get("crew") or {}
    rag_y = y.get("rag") or {}
    weav_y = rag_y.get("weaviate") or {}
    guard_y = y.get("guardrails") or {}
    eval_y = y.get("eval") or {}

    # LLM Service Configuration
    llm_model = os.getenv("LLM_MODEL", llm_y.get("model", "qwen2.5:3b"))
    if llm_model.startswith("ollama/"):
        llm_model = llm_model.replace("ollama/", "")
    
    llm_host = os.getenv("OLLAMA_HOST", llm_y.get("host", "http://ollama:11434"))

    llm = LLMConfig(
        provider=llm_y.get("provider", "ollama"),
        model=llm_model,
        host=llm_host,
    )

    # Agent LLM Configuration
    agent_temp = float(os.getenv("AGENT_TEMPERATURE", agent_llm_y.get("temperature", 0.3)))
    agent_max_iter = int(os.getenv("AGENT_MAX_ITERATIONS", agent_llm_y.get("max_iterations", 1)))
    agent_verbose_env = os.getenv("AGENT_VERBOSE", "").lower()
    if agent_verbose_env:
        agent_verbose = agent_verbose_env in {"1", "true", "yes"}
    else:
        agent_verbose = bool(agent_llm_y.get("verbose", True))
    
    agent_timeout = int(os.getenv("AGENT_TIMEOUT", agent_llm_y.get("timeout", 600)))

    agent_llm = AgentLLMConfig(
        temperature=agent_temp,
        max_iterations=agent_max_iter,
        verbose=agent_verbose,
        timeout=agent_timeout,
    )

    # Crew Configuration
    crew_process = os.getenv("CREW_PROCESS", crew_y.get("process", "sequential"))
    crew_memory_env = os.getenv("CREW_MEMORY", "").lower()
    if crew_memory_env:
        crew_memory = crew_memory_env in {"1", "true", "yes"}
    else:
        crew_memory = bool(crew_y.get("memory", False))
    
    crew_cache_env = os.getenv("CREW_CACHE", "").lower()
    if crew_cache_env:
        crew_cache = crew_cache_env in {"1", "true", "yes"}
    else:
        crew_cache = bool(crew_y.get("cache", True))

    crew = CrewConfig(
        process=crew_process,
        memory=crew_memory,
        cache=crew_cache,
    )

    agents = AgentsConfig(llm=agent_llm, crew=crew)

    # RAG Configuration
    rag_backend = os.getenv("RAG_BACKEND", rag_y.get("backend", "weaviate"))
    rag_chunk_size = int(os.getenv("RAG_CHUNK_SIZE", rag_y.get("chunk_size", 350)))
    rag_chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", rag_y.get("chunk_overlap", 60)))
    rag_top_k = int(os.getenv("RAG_TOP_K", rag_y.get("top_k", 5)))

    rag_chunk_size = max(1, rag_chunk_size)
    rag_chunk_overlap = max(0, rag_chunk_overlap)
    rag_top_k = max(1, rag_top_k)

    allow_reset_env = os.getenv("ALLOW_SCHEMA_RESET", "").lower()
    allow_reset = allow_reset_env in {"1", "true", "yes"}

    rag = RAGConfig(
        backend=rag_backend,
        chunk_size=rag_chunk_size,
        chunk_overlap=rag_chunk_overlap,
        top_k=rag_top_k,
        allow_schema_reset=allow_reset,
    )

    # Weaviate Configuration
    weav_url = os.getenv("WEAVIATE_URL", weav_y.get("url", "http://weaviate:8080"))
    weav_api_key = os.getenv("WEAVIATE_API_KEY", weav_y.get("api_key") or "") or None
    weav_index_name = os.getenv("WEAVIATE_INDEX_NAME", weav_y.get("index_name", "research_assistant"))
    weav_text_key = os.getenv("WEAVIATE_TEXT_KEY", weav_y.get("text_key", "content"))
    weav_embedding_model = os.getenv(
        "WEAVIATE_EMBEDDING_MODEL",
        weav_y.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
    )

    weaviate = WeaviateConfig(
        url=weav_url,
        api_key=weav_api_key,
        index_name=weav_index_name,
        text_key=weav_text_key,
        embedding_model=weav_embedding_model,
    )

    # Guardrails Configuration
    citation_required_env = os.getenv("GUARDRAILS_CITATION_REQUIRED")
    if citation_required_env is not None:
        citation_required = citation_required_env.lower() in {"1", "true", "yes"}
    else:
        citation_required = bool(guard_y.get("citation_required", True))
    
    strict_mode_env = os.getenv("GUARDRAILS_STRICT_MODE")
    if strict_mode_env is not None:
        strict_mode = strict_mode_env.lower() in {"1", "true", "yes"}
    else:
        strict_mode = bool(guard_y.get("strict_mode", False))

    guardrails = GuardrailsConfig(
        citation_required=citation_required,
        strict_mode=strict_mode,
    )

    # Evaluation Configuration
    faithfulness_metric = os.getenv(
        "EVAL_FAITHFULNESS_METRIC",
        eval_y.get("faithfulness_metric", "trulens_groundedness"),
    )
    
    enable_trulens_env = os.getenv("EVAL_ENABLE_TRULENS")
    if enable_trulens_env is not None:
        enable_trulens = enable_trulens_env.lower() in {"1", "true", "yes"}
    else:
        enable_trulens = bool(eval_y.get("enable_trulens", True))
    
    enable_performance_env = os.getenv("EVAL_ENABLE_PERFORMANCE")
    if enable_performance_env is not None:
        enable_performance = enable_performance_env.lower() in {"1", "true", "yes"}
    else:
        enable_performance = bool(eval_y.get("enable_performance_tracking", True))

    eval_cfg = EvalConfig(
        faithfulness_metric=faithfulness_metric,
        enable_trulens=enable_trulens,
        enable_performance_tracking=enable_performance,
    )

    return AppConfig(
        llm=llm,
        agents=agents,
        rag=rag,
        weaviate=weaviate,
        guardrails=guardrails,
        eval=eval_cfg,
    )