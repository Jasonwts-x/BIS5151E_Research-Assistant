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
    """Result from crew execution."""

    topic: str
    language: str
    final_output: str
    context_docs: List[Document]
    evaluation: Dict[str, Any] = None


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
                "Failed to initialize RAG pipeline: %s. Crew will run without context.",
                e,
            )
            self.rag_pipeline = None
        
        # Initialize CrewAI LLM for Ollama
        self.llm = LLM(
            model=f"ollama/{self.config.llm.model}",
            base_url=self.config.llm.host,
            temperature=0.3,
        )
        logger.info(
            "LLM initialized: ollama/%s at %s", 
            self.config.llm.model, 
            self.config.llm.host
        )

        # Initialize new guardrails validators
        if enable_guardrails:
            try:
                guardrails_config = load_guardrails_config()
                self.input_validator = InputValidator(guardrails_config)
                self.output_validator = OutputValidator(guardrails_config)
                logger.info("Safety guardrails enabled (new implementation)")
            except Exception as e:
                logger.warning("Failed to initialize guardrails: %s", e)
                self.input_validator = None
                self.output_validator = None
        else:
            self.input_validator = None
            self.output_validator = None
            logger.info("Safety guardrails disabled")

        # Initialize new TruLens client
        if enable_monitoring:
            try:
                self.trulens_client = TruLensClient(enabled=True)
                logger.info("TruLens monitoring enabled")
            except Exception as e:
                logger.warning("Failed to initialize TruLens: %s", e)
                self.trulens_client = None
        else:
            self.trulens_client = None
            logger.info("TruLens monitoring disabled")

        # Initialize performance tracker
        self.performance_tracker = PerformanceTracker()

    def __del__(self):
        """Cleanup: Close Weaviate connection if it exists."""
        if self.rag_pipeline is not None:
            try:
                self.rag_pipeline.close()
            except Exception:
                pass

    def retrieve_context(self, topic: str) -> tuple[str, List[Document]]:
        """
        Retrieve relevant context from RAG pipeline.
    
        Args:
            topic: Query topic
        
        Returns:
            Tuple of (formatted_context_string, list_of_documents)
        """
        # Check if RAG pipeline is available
        if self.rag_pipeline is None:
            logger.warning("RAG pipeline not initialized - returning empty context")
            return "No context available (RAG pipeline not initialized).", []
    
        try:
            with self.performance_tracker.track("rag_retrieval"):
                # Get top-k documents
                top_k = self.config.rag.top_k
                logger.info("Retrieving top-%d documents for topic: %s", top_k, topic)
            
                docs = self.rag_pipeline.run(query=topic, top_k=top_k)
            
                logger.info("Retrieved %d documents from RAG", len(docs))
            
                # Format context
                context = self._format_context(docs)
            
                return context, docs
            
        except Exception as e:
            logger.exception("RAG retrieval failed: %s", e)
            return f"Context retrieval failed: {str(e)}", []

    def _format_context(self, documents: List[Document]) -> str:
        """Format documents with citation numbers."""
        if not documents:
            return "NO CONTEXT AVAILABLE"
        
        source_map = {}
        source_counter = 1
        
        for doc in documents:
            source = doc.meta.get("source", "unknown")
            if source not in source_map:
                source_map[source] = source_counter
                source_counter += 1
        
        formatted_chunks = []
        for doc in documents:
            source = doc.meta.get("source", "unknown")
            citation_num = source_map[source]
            
            formatted_chunks.append(
                f"SOURCE [{citation_num}] ({source}):\n{doc.content}\n"
            )
        
        context = "\n---\n".join(formatted_chunks)
        context += "\n\n=== SOURCES ===\n"
        for source, num in sorted(source_map.items(), key=lambda x: x[1]):
            context += f"[{num}] {source}\n"
        
        return context

    def run(self, topic: str, language: str = "en") -> CrewResult:
        """Execute the full crew workflow."""
        logger.info("Starting crew run for topic: %s (language: %s)", topic, language)
        
        self.performance_tracker.start()

        # Input validation using new guardrails
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
        
        # Step 2: Initialize crew with LLM
        crew = ResearchCrew(llm=self.llm)
        
        # Step 3: Execute crew workflow with performance tracking
        logger.info("Executing crew workflow...")
        
        with self.performance_tracker.track("crew_execution"):
            final_output = crew.run(topic=topic, context=context, language=language)
        
        logger.info("Crew workflow completed. Output length: %d chars", len(final_output))
        
        # ✅ Output validation using new guardrails
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
                        "TruLens evaluation complete: overall_score=%.2f",
                        trulens_result.get("overall_score", 0.0),
                    )
                except Exception as e:
                    logger.error("TruLens evaluation failed: %s", e)
                    evaluation_results["trulens"] = {"error": str(e)}
        
        # Store guardrails results to database
        if record_id and (self.input_validator or self.output_validator):
            try:
                from ..eval.database import get_database
                from ..eval.models import GuardrailsResults
                
                db = get_database()
                
                input_passed_val = True  # Already validated above
                
                guardrails_record = GuardrailsResults(
                    record_id=record_id,
                    timestamp=datetime.utcnow(),
                    input_passed=input_passed_val,
                    output_passed=output_passed,
                    overall_passed=input_passed_val and output_passed,
                    violations=[r.message for r in output_results if not r.passed and r.level.value == "error"],
                    warnings=[r.message for r in output_results if not r.passed and r.level.value == "warning"],
                )
                
                with db.get_session() as session:
                    session.add(guardrails_record)
                    session.commit()
                    
                logger.info("Stored guardrails results for record %s", record_id)
                    
            except Exception as e:
                logger.error("Failed to store guardrails results: %s", e)
        
        # Add guardrails results to evaluation
        if self.input_validator or self.output_validator:
            guardrails_summary = {
                "input_passed": True,
                "output_passed": output_passed,
            }
            
            if self.output_validator and not output_passed:
                guardrails_summary["output_warnings"] = [
                    r.message for r in output_results if not r.passed
                ]
            
            evaluation_results["guardrails"] = guardrails_summary
        
        # Stop performance tracking and add to evaluation
        self.performance_tracker.stop()
        evaluation_results["performance"] = self.performance_tracker.get_summary()
        
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
            evaluation=evaluation_results,
        )

    def save_output(self, result: CrewResult, output_base_dir: Path = None) -> dict[str, Path]:
        """Save crew output to multiple formats with keyword-based folder naming."""
        if output_base_dir is None:
            output_base_dir = Path("outputs")
        
        topic_slug = self._slugify_topic(result.topic)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{timestamp}_{topic_slug}"
        output_dir = output_base_dir / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = {}
        
        md_path = output_dir / "summary.md"
        md_content = self._format_markdown_output(result)
        md_path.write_text(md_content, encoding="utf-8")
        saved_paths["markdown"] = md_path
        
        txt_path = output_dir / "summary.txt"
        txt_path.write_text(result.final_output, encoding="utf-8")
        saved_paths["text"] = txt_path
        
        logger.info("Outputs saved to: %s", output_dir)
        return saved_paths

    def _slugify_topic(self, topic: str) -> str:
        """Convert topic to filesystem-safe slug."""
        slug = re.sub(r'[^\w\s-]', '', topic.lower())
        slug = re.sub(r'[\s_]+', '_', slug)
        slug = slug[:50]
        return slug

    def _format_markdown_output(self, result: CrewResult) -> str:
        """Format result as markdown."""
        md = f"# Research Summary: {result.topic}\n\n"
        md += f"**Language:** {result.language}\n"
        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**Sources:** {len(result.context_docs)} documents\n\n"
        md += "---\n\n"
        md += result.final_output
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


_crew_runner = None


def get_crew_runner() -> CrewRunner:
    """Get singleton CrewRunner instance."""
    global _crew_runner
    if _crew_runner is None:
        _crew_runner = CrewRunner(
            enable_guardrails=True,
            enable_monitoring=True,
        )
    return _crew_runner