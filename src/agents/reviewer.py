from __future__ import annotations

import logging

from .base import AgentConfig, BaseAgent

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    """Improves coherence, structure, and style of the draft."""

    def run(self, draft: str) -> str:
        instructions = (
            "You are a peer reviewer.\n"
            "- Improve clarity, coherence, and flow.\n"
            "- Keep the meaning and claims.\n"
            "- Use concise academic language.\n"
            "- Do not invent new references or facts."
        )

        task = "Rewrite the following draft to improve clarity, coherence, and style."

        prompt = self.build_prompt(
            task=task,
            context=f"Draft:\n{draft}",
            instructions=instructions,
        )

        logger.info("ReviewerAgent: reviewing draft of length %d", len(draft))
        return self._call_llm(prompt)


def default_reviewer() -> ReviewerAgent:
    cfg = AgentConfig(
        name="reviewer",
        role="reviews and improves draft",
        model="llama3",
        system_prompt="You are a careful academic reviewer.",
        temperature=0.2,
    )
    return ReviewerAgent(cfg)
