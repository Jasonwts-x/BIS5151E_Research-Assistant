from __future__ import annotations

import logging
from typing import Optional

from .base import AgentConfig, BaseAgent

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Drafts an initial literature summary."""

    def run(self, topic: str, context: Optional[str] = None) -> str:
        # Context handling: either real retrieved context or an explicit note
        if context:
            ctx = f"You may use this retrieved context:\n{context}"
        else:
            ctx = "No external context was provided."

        instructions = (
            "You are an academic writer.\n"
            "- Use a neutral, academic tone.\n"
            "- Focus on 5–8 sentences.\n"
            "- If citations are mentioned, keep them generic (e.g., 'recent studies')."
        )

        task = f"Write a concise literature-style summary on the topic: '{topic}'."

        prompt = self.build_prompt(
            task=task,
            context=ctx,
            instructions=instructions,
        )

        logger.info("WriterAgent: generating draft for topic '%s'", topic)
        return self._call_llm(prompt)


def default_writer() -> WriterAgent:
    """Factory using global config but allowing per-agent overrides via env later."""
    cfg = AgentConfig(
        name="writer",
        role="drafts initial literature summary",
        model="llama3",  # could later be read from env/YAML
        system_prompt="You are a helpful academic writing assistant.",
        temperature=0.3,
    )
    return WriterAgent(cfg)
