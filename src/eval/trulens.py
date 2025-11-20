from __future__ import annotations


class TruLensEvaluator:
    """
    Placeholder for TruLens evaluation.

    Later responsibilities:
    - record LLM calls and context,
    - compute faithfulness / relevance scores,
    - help us compare different RAG / agent configurations.
    """

    def score(self, query: str, answer: str) -> dict:
        # Phase-0: no-op, return dummy score
        return {"faithfulness": None, "relevance": None}
