from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from typing import Dict, Optional

from .base import BaseAgent
from .factchecker import default_factchecker
from .reviewer import default_reviewer
from .translator import default_translator
from .writer import default_writer

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    topic: str
    language: str
    writer_output: str
    reviewed_output: str
    checked_output: str
    final_output: str
    timing: Dict[str, float]


class Orchestrator:
    """Coordinates Writer → Reviewer → FactChecker → (optional) Translator."""

    def __init__(
        self,
        writer: BaseAgent,
        reviewer: BaseAgent,
        factchecker: BaseAgent,
        translator: Optional[BaseAgent] = None,
    ) -> None:
        self.writer = writer
        self.reviewer = reviewer
        self.factchecker = factchecker
        self.translator = translator

    def run_pipeline(
        self,
        topic: str,
        language: str = "en",
        context: Optional[str] = None,
    ) -> PipelineResult:
        logger.info("Pipeline: starting for topic='%s' (language=%s)", topic, language)
        timings: Dict[str, float] = {}

        # ---------- Writer ----------
        t0 = time.time()
        draft = self._run_step(
            "writer", lambda: self.writer.run(topic=topic, context=context)
        )
        timings["writer"] = time.time() - t0

        # ---------- Reviewer ----------
        t0 = time.time()
        reviewed = self._run_step("reviewer", lambda: self.reviewer.run(draft=draft))
        timings["reviewer"] = time.time() - t0

        # ---------- FactChecker ----------
        t0 = time.time()
        checked = self._run_step(
            "factchecker", lambda: self.factchecker.run(text=reviewed, context=context)
        )
        timings["factchecker"] = time.time() - t0

        # ---------- Translator ----------
        if language.lower() != "en" and self.translator:
            t0 = time.time()
            final = self._run_step(
                "translator",
                lambda: self.translator.run(text=checked, target_language=language),
            )
            timings["translator"] = time.time() - t0
        else:
            final = checked
            timings["translator"] = 0.0

        return PipelineResult(
            topic=topic,
            language=language,
            writer_output=draft,
            reviewed_output=reviewed,
            checked_output=checked,
            final_output=final,
            timings=timings,
        )

    def _run_step(self, name: str, fn):
        try:
            logger.info("Pipeline step '%s' started...", name)
            output = fn()
            logger.info("Pipeline step '%s' completed.", name)
            return output
        except Exception as exc:
            logger.error("Pipeline step '%s' failed: %s", name, exc)
            raise


def default_orchestrator() -> Orchestrator:
    """Factory used by API and CLI."""
    return Orchestrator(
        writer=default_writer(),
        reviewer=default_reviewer(),
        factchecker=default_factchecker(),
        translator=default_translator(),
    )


def serialize_result(result: PipelineResult) -> dict:
    """Small helper for API responses."""
    return asdict(result)
