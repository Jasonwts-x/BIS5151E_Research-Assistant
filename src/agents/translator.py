from __future__ import annotations

import logging

from .base import AgentConfig, BaseAgent

logger = logging.getLogger(__name__)


class TranslatorAgent(BaseAgent):
    """Translates the final checked text into a target language."""

    def run(self, text: str, target_language: str) -> str:
        instructions = (
            "You are a professional academic translator.\n"
            "- Preserve meaning and nuance.\n"
            "- Keep citations like [1], [2] exactly as they are.\n"
            "- Maintain an academic writing style in the target language."
        )

        task = f"Translate the following text into {target_language}."

        prompt = self.build_prompt(
            task=task,
            context=f"Text:\n{text}",
            instructions=instructions,
        )

        logger.info(
            "TranslatorAgent: translating text of length %d to '%s'",
            len(text),
            target_language,
        )
        return self._call_llm(prompt)


def default_translator() -> TranslatorAgent:
    cfg = AgentConfig(
        name="translator",
        role="translates checked summary into target language",
        model="llama3",  # later: swap to DeepL API instead of LLM
        system_prompt="You specialise in translating academic texts.",
        temperature=0.0,
    )
    return TranslatorAgent(cfg)
