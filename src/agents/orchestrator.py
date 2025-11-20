from __future__ import annotations

from dataclasses import dataclass

from ..rag.service import RAGService
from .factchecker import FactCheckerAgent
from .reviewer import ReviewerAgent
from .translator import TranslatorAgent
from .writer import WriterAgent


@dataclass
class Orchestrator:
    """
    Simple in-code multi-agent orchestrator.

    Phase-0: writer -> reviewer -> fact-checker
    Later: this will be mirrored / controlled via n8n workflows.
    """

    writer: WriterAgent
    reviewer: ReviewerAgent
    factchecker: FactCheckerAgent
    translator: TranslatorAgent

    @classmethod
    def default(cls) -> "Orchestrator":
        rag = RAGService()
        return cls(
            writer=WriterAgent(rag=rag),
            reviewer=ReviewerAgent(),
            factchecker=FactCheckerAgent(),
            translator=TranslatorAgent(),
        )

    def run_topic(self, topic: str, translate_to: str | None = None) -> str:
        draft = self.writer.draft(topic)
        reviewed = self.reviewer.review(draft)
        checked = self.factchecker.check(reviewed)

        if translate_to:
            checked = self.translator.translate(
                checked, target_lang=translate_to)

        return checked
