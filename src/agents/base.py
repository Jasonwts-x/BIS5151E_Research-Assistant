from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ollama import chat

from ..utils.config import load_config

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Lightweight config for each agent."""

    name: str
    role: str
    model: Optional[str] = None
    system_prompt: str = ""
    temperature: float = 0.3


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        app_cfg = load_config()

        if self.config.model is None:
            self.config.model = app_cfg.llm.model

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        """Execute the agent's main behaviour."""

    def build_prompt(
        self,
        task: str,
        context: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> str:
        """Build a basic structured prompt."""

        parts: list[str] = []

        if instructions:
            parts.append(instructions)
            parts.append("")

        parts.append(f"Task:\n{task}")

        if context:
            parts.append("")
            parts.append(f"Context:\n{context}")

        return "\n".join(parts)

    def _call_llm(self, user_prompt: str) -> str:
        """Call Ollama with per-agent settings."""

        if not self.config.model:
            msg = "AgentConfig.model is not set and no global model is available."
            logger.error("%s (agent=%s)", msg, self.config.name)
            raise RuntimeError(msg)

        logger.info("Agent %s calling model %s", self.config.name, self.config.model)

        messages = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        options: Dict[str, Any] = {}
        if self.config.temperature is not None:
            options["temperature"] = self.config.temperature

        try:
            res = chat(
                model=self.config.model,
                messages=messages,
                options=options or None,
            )
        except Exception as exc:
            logger.error(
                "Agent '%s' failed to call model '%s': %s",
                self.config.name,
                self.config.model,
                exc,
            )
            raise

        content = getattr(getattr(res, "message", None), "content", "")
        if not content:
            msg = (
                f"Ollama returned an empty response "
                f"(agent={self.config.name}, model={self.config.model})"
            )
            logger.error(msg)
            raise RuntimeError(msg)

        return content
