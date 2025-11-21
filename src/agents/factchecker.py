from __future__ import annotations

import logging
from typing import Optional

from .base import AgentConfig, BaseAgent

logger = logging.getLogger(__name__)


class FactCheckerAgent(BaseAgent):
    """
    Validates claims and enforces citation discipline.
    For now this is LLM-only; later we will connect it to RAG + Guardrails/TruLens.
    """

    def run(self, text: str, context: Optional[str] = None) -> str:
        if context:
            ctx = (
                "Here is external context you MUST rely on when checking claims:\n"
                f"{context}"
            )
        else:
            ctx = "No verified external context was provided."

        instructions = (
            "You are a fact-checking and citation assistant.\n"
            "Your tasks:\n"
            "1. Check the text for clearly unsupported or speculative claims.\n"
            "2. If something is likely wrong, soften wording or flag it as uncertain.\n"
            "3. Ensure that citations like [1], [2] are consistent and not fabricated.\n"
            "4. Do NOT invent new sources."
        )

        task = "Review the following text for factual issues and citation consistency."

        prompt = self.build_prompt(
            task=task,
            context=f"{ctx}\n\nText to verify:\n{text}",
            instructions=instructions,
        )

        logger.info("FactCheckerAgent: validating text of length %d", len(text))
        return self._call_llm(prompt)


def default_factchecker() -> FactCheckerAgent:
    cfg = AgentConfig(
        name="factchecker",
        role="checks factual consistency and citations",
        model="llama3",
        system_prompt="You are a rigorous fact-checking assistant.",
        temperature=0.1,
    )
    return FactCheckerAgent(cfg)
