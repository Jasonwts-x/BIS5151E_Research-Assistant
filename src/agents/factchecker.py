from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FactCheckerAgent:
    """
    Validates claims and checks references.

    Phase-0: placeholder that just returns the input unchanged.
    Later: will use RAG + Guardrails + TruLens signals.
    """

    def check(self, text: str) -> str:
        # TODO: add fact-checking logic with RAG + evaluation.
        return text
