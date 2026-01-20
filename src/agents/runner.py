from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from crewai import LLM
from haystack.dataclasses import Document

from ..rag.core import RAGPipeline
from ..utils.config import load_config
from .crews import ResearchCrew

logger = logging.getLogger(__name__)


@dataclass
class CrewResult:
    """Result from crew execution."""

    topic: str
    language: str
    final_output: str
    context_docs: List[Document]


class CrewRunner:
    """
    Orchestrates RAG retrieval + CrewAI execution.
    
    This is the main entry point for running the agentic workflow.
    """

    def __init__(self):
        """Initialize runner with RAG pipeline and LLM."""
        self.config = load_config()
        
        # Initialize RAG pipeline for retrieval
        try:
            from ..rag.core import RAGPipeline
            self.rag_pipeline = RAGPipeline.from_existing()
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.warning(
                "Failed to initialize RAG pipeline: %s. Crew will run without context.", e
            )
            self.rag_pipeline = None
        
        # Initialize CrewAI LLM for Ollama
        # CrewAI's LLM class uses LiteLLM internally for provider abstraction
        self.llm = LLM(
            model=f"ollama/{self.config.llm.model}",  # LiteLLM format: "provider/model"
            base_url=self.config.llm.host,
            temperature=0.3,
            timeout=900, # 15 minutes # TODO: Change to 300 (5 minutes)
        )
        logger.info(
            "LLM initialized: ollama/%s at %s", 
            self.config.llm.model, 
            self.config.llm.host
        )

    def retrieve_context(self, topic: str) -> tuple[str, List[Document]]:
        """
        Retrieve relevant documents from RAG pipeline.
        
        Args:
            topic: Research topic/question
            
        Returns:
            Tuple of (formatted_context_string, list_of_documents)
        """
        if self.rag_pipeline is None:
            logger.warning("RAG pipeline not available, returning empty context")
            return "No context available.", []
        
        top_k = self.config.rag.top_k
        docs = self.rag_pipeline.run(query=topic, top_k=top_k)
        
        logger.info("Retrieved %d documents for topic: %s", len(docs), topic)
        
        # Format context for agents
        context = self._format_context(docs)
        return context, docs

    @staticmethod
    def _format_context(docs: List[Document]) -> str:
        """
        Format retrieved documents into context string with citations.
        
        Args:
            docs: List of Haystack Documents
            
        Returns:
            Formatted context string with [1], [2], etc. citations
        """
        if not docs:
            return "No external context was retrieved."
        
        unique_sources = []
        lines = []
        
        for doc in docs:
            meta = getattr(doc, "meta", {}) or {}
            source = meta.get("source", "unknown")
            
            # Track unique sources
            if source not in unique_sources:
                unique_sources.append(source)
            
            idx = unique_sources.index(source) + 1
            lines.append(f"[{idx}] {doc.content.strip()}")
        
        context = "\n\n".join(lines)
        source_map = "\n".join(f"[{i+1}] {s}" for i, s in enumerate(unique_sources))
        
        return f"{context}\n\nSources:\n{source_map}"

    def run(self, topic: str, language: str = "en") -> CrewResult:
        """
        Execute the full crew workflow.
        
        Args:
            topic: Research topic/question
            language: Target language (currently only 'en' supported)
            
        Returns:
            CrewResult with final output and metadata
        """
        logger.info("Starting crew run for topic: %s (language: %s)", topic, language)
        
        # Step 1: Retrieve context from RAG
        context, docs = self.retrieve_context(topic)
        
        # Step 2: Initialize crew with LLM
        crew = ResearchCrew(llm=self.llm)
        
        # Step 3: Execute crew workflow
        logger.info("Executing crew workflow...")
        final_output = crew.run(topic=topic, context=context)
        
        logger.info("Crew workflow completed. Output length: %d chars", len(final_output))
        
        # TODO: Translation support for language != 'en'
        # This will be added in Step H (DeepL integration)
        if language.lower() != "en":
            logger.warning(
                "Translation not yet implemented. Returning English output. "
                "Requested language: %s",
                language,
            )
        
        return CrewResult(
            topic=topic,
            language=language,
            final_output=final_output,
            context_docs=docs,
        )


def get_crew_runner() -> CrewRunner:
    """Factory function for dependency injection."""
    return CrewRunner()