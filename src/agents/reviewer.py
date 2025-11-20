from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReviewerAgent:
    """
    Reviews and polishes the draft.

    Phase-0: just echoes the text.
    Later: will call an LLM to improve coherence, structure, and style.
    """

    def review(self, draft: str) -> str:
        # TODO: call LLM for rewriting in a later phase.
        return draft
