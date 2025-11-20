from __future__ import annotations

from typing import Optional

from ollama import chat

from ..utils.config import load_config


def local_llm_query(prompt: str, model: Optional[str] = None) -> str:
    """
    Minimal test for Ollama integration with a safety net.
    Uses model from config if not provided.
    """
    cfg = load_config()
    model_name = model or cfg.llm.model

    try:
        res = chat(model=model_name, messages=[{"role": "user", "content": prompt}])
        return res.message.content
    except Exception as e:
        host = cfg.llm.host
        return (
            "❌ Could not reach Ollama.\n"
            f"- Host: {host}\n"
            f"- Model: {model_name}\n"
            f"- Error: {e}"
        )


if __name__ == "__main__":
    print(local_llm_query("Summarize the purpose of generative AI in one sentence."))
