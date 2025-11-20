from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..utils.config import AppConfig, load_config
from .query import local_llm_query


@dataclass
class RAGService:
    """
    Phase-0 RAG facade.

    Right now this is a very thin wrapper around `local_llm_query`.
    In later phases, we'll plug in Haystack RAG pipelines here.
    """

    config: Optional[AppConfig] = None

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = load_config()

    def generate_summary(self, topic: str, max_sentences: int | None = 8) -> str:
        max_s = max_sentences or 8
        prompt = (
            "You are an academic research assistant.\n"
            f"Write a concise literature-style overview in at most {max_s} sentences\n"
            f"about the topic: '{topic}'.\n"
            "Focus on definitions, goals, and typical challenges. "
            "For now you may use generic references like [Author, Year]; "
            "later this will be replaced by real citations from our RAG pipeline."
        )
        return local_llm_query(prompt, model=self.config.llm.model)
