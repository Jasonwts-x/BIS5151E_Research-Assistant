from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from crewai import LLM
from haystack.dataclasses import Document


from ..eval.guardrails import GuardrailsWrapper
from ..eval.trulens import TruLensMonitor
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

    def __init__(self, enable_guardrails: bool = True, enable_monitoring: bool = False):
        """
        Initialize runner with RAG pipeline, LLM, and optional safety/monitoring.

        Args:
            enable_guardrails: Enable safety checks on inputs/outputs
            enable_monitoring: Enable TruLens monitoring (requires trulens-eval)
        """
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
        self.llm = LLM(
            model=f"ollama/{self.config.llm.model}",
            base_url=self.config.llm.host,
            temperature=0.3,  # Lower temperature for more factual outputs
        )
        logger.info(
            "LLM initialized: ollama/%s at %s", 
            self.config.llm.model, 
            self.config.llm.host
        )

        # Initialize safety guardrails
        self.guardrails = GuardrailsWrapper() if enable_guardrails else None
        if self.guardrails:
            logger.info("Safety guardrails enabled")
        else:
            logger.info("Safety guardrails disabled")

        # Initialize TruLens monitoring
        self.monitor = TruLensMonitor(enabled=enable_monitoring)

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
        
        # Format context for agents (with stricter formatting)
        context = self._format_context(docs)
        return context, docs

    @staticmethod
    def _format_context(docs: List[Document]) -> str:
        """
        Format retrieved documents into context string with prominent citations.
        
        This formatting makes it VERY clear what sources are available and what
        content belongs to each source.
        
        Args:
            docs: List of Haystack Documents
            
        Returns:
            Formatted context string with [1], [2], etc. citations
        """
        if not docs:
            return (
                "⚠️ NO CONTEXT AVAILABLE ⚠️\\n"
                "No documents were retrieved for this topic.\\n"
                "You CANNOT write a summary without sources.\\n"
                "Inform the user that no relevant documents were found."
            )
        
        unique_sources = []
        context_blocks = []
        
        # Group content by source
        for doc in docs:
            meta = getattr(doc, "meta", {}) or {}
            source = meta.get("source", "unknown")
            
            # Track unique sources
            if source not in unique_sources:
                unique_sources.append(source)
            
            idx = unique_sources.index(source) + 1
            content = doc.content.strip() if doc.content else "[No content]"
            
            # Format each chunk with clear source marking
            context_blocks.append(
                f"═══════════════════════════════════════\\n"
                f"SOURCE [{idx}]: {source}\\n"
                f"═══════════════════════════════════════\\n"
                f"{content}\\n"
            )
        
        # Build final context with clear sections
        context_body = "\\n".join(context_blocks)
        
        source_list = "\\n".join(
            f"  [{i+1}] {s}" for i, s in enumerate(unique_sources)
        )
        
        header = (
            "╔═══════════════════════════════════════════════════════════════╗\\n"
            "║   AVAILABLE SOURCES - USE ONLY THESE IN YOUR RESPONSE        ║\\n"
            "╚═══════════════════════════════════════════════════════════════╝\\n"
            f"\\n{source_list}\\n\\n"
            "⚠️ CRITICAL: You may ONLY cite sources listed above.\\n"
            "⚠️ Do NOT invent additional sources or citations.\\n"
            "⚠️ Every factual claim must reference one of these sources.\\n\\n"
        )
        
        return f"{header}{context_body}"

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

        # Safety check: Validate input
        if self.guardrails:
            is_safe, reason = self.guardrails.validate_input(topic)
            if not is_safe:
                logger.error("Input validation failed: %s", reason)
                return CrewResult(
                    topic=topic,
                    language=language,
                    final_output=f"⚠️ Safety check failed: {reason}",
                    context_docs=[]
                )
        
        # Step 1: Retrieve context from RAG
        context, docs = self.retrieve_context(topic)
        
        # Log warning if no documents found
        if not docs:
            logger.warning(
                "No documents retrieved for topic '%s'. "
                "Consider running ArXiv ingestion first: POST /rag/ingest/arxiv",
                topic
            )
        
        # Step 2: Initialize crew with LLM
        crew = ResearchCrew(llm=self.llm)
        
        # Step 3: Execute crew workflow
        logger.info("Executing crew workflow...")
        final_output = crew.run(
            topic=topic, context=context, language=language)
        
        logger.info(
            "Crew workflow completed. Output length: %d chars", len(final_output))
        
        # Safety check: Validate output
        if self.guardrails:
            is_safe, reason = self.guardrails.validate_output(final_output)
            if not is_safe:
                logger.error("Output validation failed: %s", reason)
                final_output = f"⚠️ Response blocked due to safety policy: {reason}"

        # Monitoring: Log interaction
        if self.monitor:
            self.monitor.log_interaction(
                topic=topic,
                context=context,
                output=final_output,
                language=language
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