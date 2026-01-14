from __future__ import annotations

from ..utils.config import load_config


def main() -> None:
    """CLI bootstrap to verify configuration & environment."""
    cfg = load_config()

    print("✅ ResearchAssistantGPT bootstrap")
    print(f"LLM provider: {cfg.llm.provider}")
    print(f"LLM model: {cfg.llm.model}")
    print(f"LLM host: {cfg.llm.host}")
    print(
        "RAG:",
        {
            "chunk_size": cfg.rag.chunk_size,
            "chunk_overlap": cfg.rag.chunk_overlap,
            "top_k": cfg.rag.top_k,
        },
    )
    print("\nUseful commands:")
    print("- uvicorn src.app.server:app --reload --host 0.0.0.0 --port 8000")
    print("- curl http://localhost:8000/health")
    print(
        '- curl -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -d \'{"query":"...", "language":"en"}\''
    )


if __name__ == "__main__":
    main()
