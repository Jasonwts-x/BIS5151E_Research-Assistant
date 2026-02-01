"""
CrewAI Runner.

Main orchestrator for RAG + CrewAI workflow execution.
Manages RAG retrieval, agent execution, evaluation, and output generation.

Architecture:
    Singleton pattern - initializes components once and reuses them.
    Coordinates: RAG Pipeline → Crew Execution → Evaluation → Output.
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from crewai import LLM
from haystack.dataclasses import Document

from ..rag.core.pipeline import RAGPipeline
from ..eval.guardrails import InputValidator, OutputValidator, load_guardrails_config
from ..eval.performance import PerformanceTracker
from ..eval.trulens import TruLensClient
from ..utils.config import load_config
from .crews import ResearchCrew

logger = logging.getLogger(__name__)


@dataclass
class CrewResult:
    """
    Result from crew execution.
    
    Attributes:
        topic: Research topic/query
        language: Target language code
        final_output: Final generated summary
        context_docs: Retrieved documents from RAG
        evaluation: Evaluation metrics (performance, TruLens, guardrails)
    """
    topic: str
    language: str
    final_output: str
    context_docs: List[Document]
    evaluation: Dict[str, Any] = None


class CrewRunner:
    """
    Orchestrates RAG retrieval + CrewAI execution.
    
    Main entry point for the agentic workflow. Initializes all components once
    (singleton pattern) and reuses them across requests for better performance.
    
    Attributes:
        config: Application configuration
        rag_pipeline: RAG pipeline for document retrieval
        llm: Language model instance
        crew: ResearchCrew instance
        input_validator: Input safety validator
        output_validator: Output safety validator
        trulens_client: TruLens evaluation client
        performance_tracker: Performance metrics tracker
    """

    def __init__(self, enable_guardrails: bool = True, enable_monitoring: bool = False):
        """
        Initialize runner with RAG pipeline, LLM, crew, and optional safety/monitoring.

        Args:
            enable_guardrails: Enable safety checks on inputs/outputs
            enable_monitoring: Enable TruLens monitoring
        """
        logger.info("Initializing CrewRunner...")
        
        self.config = load_config()
        self.rag_pipeline = None  # Initialize to None first
        
        # Initialize RAG pipeline for document retrieval
        # Uses try-except because RAG might not be available in all environments
        try:
            self.rag_pipeline = RAGPipeline.from_existing()
            logger.info("✓ RAG pipeline initialized successfully")
        except Exception as e:
            logger.warning(
                "Failed to initialize RAG pipeline: %s.", e
            )
            logger.info(
                "RAG pipeline will be initialized on first use. "
                "Collection will be created when you run ingestion."
            )
            self.rag_pipeline = None
        
        # Initialize LLM
        try:
            llm_host = self.config.llm.host
            llm_model = self.config.llm.model
            agent_temperature = self.config.agents.llm.temperature
            
            self.llm = LLM(
                model=f"ollama/{llm_model}",
                base_url=llm_host,
                temperature=agent_temperature,
            )
            logger.info("✓ LLM initialized: %s at %s", llm_model, llm_host)
        except Exception as e:
            # If LLM init fails, clean up pipeline before re-raising
            if self.rag_pipeline is not None:
                try:
                    self.rag_pipeline.close()
                except Exception:
                    pass
            raise RuntimeError(f"Failed to initialize LLM: {e}") from e
        
        # Initialize crew (reused across requests)
        try:
            self.crew = ResearchCrew(self.llm)
            logger.info("✓ ResearchCrew initialized")
        except Exception as e:
            # Clean up on failure
            if self.rag_pipeline is not None:
                try:
                    self.rag_pipeline.close()
                except Exception:
                    pass
            raise RuntimeError(f"Failed to initialize crew: {e}") from e
        
        # Initialize optional safety and monitoring components
        self.input_validator = None
        self.output_validator = None
        self.trulens_client = None
        
        if enable_guardrails:
            try:
                guardrails_config = load_guardrails_config()
                self.input_validator = InputValidator(guardrails_config)
                self.output_validator = OutputValidator(guardrails_config)
                logger.info("✓ Guardrails enabled")
            except Exception as e:
                logger.warning("Failed to initialize guardrails: %s", e)
        
        if enable_monitoring:
            try:
                self.trulens_client = TruLensClient(enabled=True)
                logger.info("✓ TruLens monitoring enabled")
            except Exception as e:
                logger.warning("Failed to initialize TruLens: %s", e)
        
        # Performance tracker
        self.performance_tracker = PerformanceTracker()
        
        logger.info("=" * 70)
        logger.info("CrewRunner initialization complete")
        logger.info("  RAG: %s", "enabled" if self.rag_pipeline else "disabled")
        logger.info("  Guardrails: %s", "enabled" if self.input_validator else "disabled")
        logger.info("  Monitoring: %s", "enabled" if self.trulens_client else "disabled")
        logger.info("  Crew: singleton (reused across requests)")
        logger.info("=" * 70)

    def __del__(self):
        """Destructor - cleanup resources."""
        self.close()

    def close(self):
        """Close and cleanup all resources."""
        if self.rag_pipeline is not None:
            try:
                self.rag_pipeline.close()
                logger.debug("RAG pipeline closed")
            except Exception as e:
                logger.warning("Error closing RAG pipeline: %s", e)

    def run(self, topic: str, language: str = "en") -> CrewResult:
        """
        Execute the full RAG + CrewAI workflow.
        
        Args:
            topic: Research topic/question
            language: Target language (en, de, fr, es, etc.)
            
        Returns:
            CrewResult with final output and evaluation metrics
        """
        logger.info("Starting crew run for topic: %s (language: %s)", topic, language)
        
        self.performance_tracker.start()

        # Input validation using guardrails
        if self.input_validator:
            with self.performance_tracker.track("guardrails_input"):
                passed, results = self.input_validator.validate(topic)
                
                if not passed:
                    errors = [r.message for r in results if not r.passed]
                    error_msg = "; ".join(errors)
                    
                    logger.error("Input validation failed: %s", error_msg)
                    self.performance_tracker.stop()
                    
                    return CrewResult(
                        topic=topic,
                        language=language,
                        final_output=f"⚠️ Safety check failed: {error_msg}",
                        context_docs=[],
                        evaluation={
                            "guardrails": {
                                "input_passed": False,
                                "violations": errors,
                            },
                            "performance": self.performance_tracker.get_summary(),
                        },
                    )
        
        # Step 1: Retrieve context from RAG
        context, docs = self.retrieve_context(topic)
        
        if not docs:
            logger.warning(
                "No documents retrieved for topic '%s'. "
                "Consider running ArXiv ingestion first: POST /rag/ingest/arxiv",
                topic
            )
        
        # Step 2: Execute crew workflow (reuse singleton crew)
        logger.info("Executing crew workflow (reusing singleton crew)...")
        
        with self.performance_tracker.track("crew_execution"):
            final_output = self.crew.run(topic=topic, context=context, language=language)
        
        logger.info("Crew workflow completed. Output length: %d chars", len(final_output))
        
        # Output validation using guardrails
        output_passed = True
        output_results = []
        
        if self.output_validator:
            with self.performance_tracker.track("guardrails_output"):
                output_passed, output_results = self.output_validator.validate(final_output)
                
                if not output_passed:
                    warnings = [r.message for r in output_results if not r.passed]
                    logger.warning("Output validation warnings: %s", "; ".join(warnings))

        # Run TruLens evaluation
        evaluation_results = {}
        record_id = None
        
        if self.trulens_client:
            with self.performance_tracker.track("trulens_evaluation"):
                try:
                    trulens_result = self.trulens_client.evaluate(
                        query=topic,
                        context=context,
                        answer=final_output,
                        language=language,
                    )
                    evaluation_results["trulens"] = trulens_result
                    record_id = trulens_result.get("record_id")
                    
                    logger.info(
                        "TruLens evaluation complete: score=%.2f, record_id=%s",
                        trulens_result.get("overall_score", 0),
                        record_id,
                    )
                except Exception as e:
                    logger.warning("TruLens evaluation failed: %s", e)
        
        # Stop performance tracker and get summary
        self.performance_tracker.stop()
        perf_summary = self.performance_tracker.get_summary()
        
        # Compile evaluation results
        evaluation_results["performance"] = perf_summary
        evaluation_results["guardrails"] = {
            "input_passed": True,  # Made it past input validation
            "output_passed": output_passed,
            "output_warnings": [r.message for r in output_results if not r.passed] if output_results else [],
        }
        
        logger.info(
            "Crew run complete: %d chars output, %.2f seconds total",
            len(final_output),
            perf_summary.get("total_time", 0),
        )
        
        return CrewResult(
            topic=topic,
            language=language,
            final_output=final_output,
            context_docs=docs,
            evaluation=evaluation_results,
        )

    def retrieve_context(self, topic: str) -> tuple[str, List[Document]]:
        """
        Retrieve relevant context from RAG pipeline.
        
        Args:
            topic: Research topic
            
        Returns:
            Tuple of (formatted_context, documents)
        """
        if self.rag_pipeline is None:
            logger.warning("RAG pipeline not initialized. No context available.")
            return "NO CONTEXT AVAILABLE: RAG pipeline not initialized.", []
        
        try:
            with self.performance_tracker.track("rag_retrieval"):
                top_k = self.config.rag.top_k
                logger.info("Retrieving top-%d documents for topic: %s", top_k, topic)
                
                docs = self.rag_pipeline.run(query=topic, top_k=top_k)
                
                logger.info("Retrieved %d documents from RAG", len(docs))
                
                context = self._format_context(docs)
                
                return context, docs
                
        except Exception as e:
            logger.exception("RAG retrieval failed: %s", e)
            return f"CONTEXT UNAVAILABLE: Error during retrieval: {e}", []

    def _format_context(self, documents: List[Document]) -> str:
        """
        Format retrieved documents with citation markers.
        
        Deduplicates sources so multiple chunks from the same document
        share the same citation number.
        
        Args:
            documents: Retrieved documents
            
        Returns:
            Formatted context string with [1], [2], etc. markers
        """
        if not documents:
            return "NO CONTEXT AVAILABLE"
        
        # Deduplicate sources (multiple chunks from same source get same citation)
        source_map = {}
        source_counter = 1
        
        for doc in documents:
            source = doc.meta.get("source", "unknown")
            if source not in source_map:
                source_map[source] = source_counter
                source_counter += 1
        
        # Format chunks with citations
        formatted_chunks = []
        for doc in documents:
            source = doc.meta.get("source", "unknown")
            citation_num = source_map[source]
            
            # Add metadata if available
            metadata_parts = []
            if "title" in doc.meta:
                metadata_parts.append(doc.meta["title"])
            if "authors" in doc.meta:
                metadata_parts.append(f"Authors: {doc.meta['authors']}")
            if "year" in doc.meta:
                metadata_parts.append(f"Year: {doc.meta['year']}")
            
            metadata_line = f"METADATA: {', '.join(metadata_parts)}" if metadata_parts else ""
            
            chunk_text = f"SOURCE [{citation_num}]: {source}\n"
            if metadata_line:
                chunk_text += f"{metadata_line}\n"
            chunk_text += f"{doc.content.strip()}\n"
            
            formatted_chunks.append(chunk_text)
        
        context = "\n---\n".join(formatted_chunks)
        
        # Add source summary at end
        context += "\n\n=== SOURCES ===\n"
        for source, num in sorted(source_map.items(), key=lambda x: x[1]):
            context += f"[{num}] {source}\n"
        
        return context

    def save_output(self, result: CrewResult, output_base_dir: Path = None) -> dict[str, Path]:
        """
        Save crew output to multiple formats.
        
        Args:
            result: CrewResult to save
            output_base_dir: Base directory for outputs
            
        Returns:
            Dictionary mapping format names to file paths
        """
        if output_base_dir is None:
            output_base_dir = Path("outputs")
        
        # Create folder with timestamp and topic slug
        topic_slug = self._slugify_topic(result.topic)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{timestamp}_{topic_slug}"
        output_dir = output_base_dir / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = {}
        
        # Save as markdown
        md_path = output_dir / "summary.md"
        md_content = self._format_markdown_output(result)
        md_path.write_text(md_content, encoding="utf-8")
        saved_paths["markdown"] = md_path
        
        # Save as plain text
        txt_path = output_dir / "summary.txt"
        txt_path.write_text(result.final_output, encoding="utf-8")
        saved_paths["text"] = txt_path
        
        logger.info("Outputs saved to: %s", output_dir)
        return saved_paths

    def _slugify_topic(self, topic: str) -> str:
        """
        Convert topic to filesystem-safe slug.
        
        Args:
            topic: Original topic string
            
        Returns:
            Filesystem-safe slug (max 50 chars)
        """
        # Remove non-alphanumeric characters
        slug = re.sub(r'[^\w\s-]', '', topic.lower())
        # Replace whitespace/underscores with single underscore
        slug = re.sub(r'[\s_]+', '_', slug)
        # Limit length
        slug = slug[:50]
        return slug

    def _format_markdown_output(self, result: CrewResult) -> str:
        """
        Format result as markdown with metadata and evaluation.
        
        Args:
            result: CrewResult to format
            
        Returns:
            Markdown-formatted string
        """
        md = f"# Research Summary: {result.topic}\n\n"
        md += f"**Language:** {result.language}\n"
        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**Sources:** {len(result.context_docs)} documents\n\n"
        md += "---\n\n"
        
        # Main output
        md += result.final_output
        
        # Add sources section
        md += "\n\n---\n\n"
        md += "## Sources\n\n"
        
        sources = set()
        for doc in result.context_docs:
            source = doc.meta.get("source", "unknown")
            sources.add(source)
        
        for i, source in enumerate(sorted(sources), 1):
            md += f"{i}. {source}\n"
        
        # Add evaluation summary
        if result.evaluation:
            md += "\n\n## Evaluation Metrics\n\n"
            
            if "performance" in result.evaluation:
                perf = result.evaluation["performance"]
                md += "### Performance\n"
                md += f"- Total Time: {perf.get('total_time', 0):.2f}s\n"
                if "components" in perf:
                    for comp, time in perf["components"].items():
                        if comp != "total_time":
                            md += f"- {comp}: {time:.2f}s\n"
                md += "\n"
            
            if "trulens" in result.evaluation:
                trulens = result.evaluation["trulens"]
                md += "### Quality Metrics (TruLens)\n"
                if "overall_score" in trulens:
                    md += f"- Overall Score: {trulens['overall_score']:.2f}\n"
                if "trulens" in trulens and isinstance(trulens["trulens"], dict):
                    for metric, value in trulens["trulens"].items():
                        if isinstance(value, (int, float)):
                            md += f"- {metric}: {value:.2f}\n"
                md += "\n"
            
            if "guardrails" in result.evaluation:
                guards = result.evaluation["guardrails"]
                md += "### Safety Validation (Guardrails)\n"
                md += f"- Input Passed: {'✅' if guards.get('input_passed') else '❌'}\n"
                md += f"- Output Passed: {'✅' if guards.get('output_passed') else '❌'}\n"
                if guards.get("output_warnings"):
                    md += "\nWarnings:\n"
                    for warning in guards["output_warnings"]:
                        md += f"- {warning}\n"
        
        return md


# ============================================================================
# Crew Runner - Singleton Instance
# ============================================================================

_crew_runner = None


def get_crew_runner() -> CrewRunner:
    """
    Get singleton CrewRunner instance.
    
    Returns:
        Global CrewRunner instance
    """
    global _crew_runner
    if _crew_runner is None:
        _crew_runner = CrewRunner(
            enable_guardrails=True,
            enable_monitoring=True,
        )
    return _crew_runner