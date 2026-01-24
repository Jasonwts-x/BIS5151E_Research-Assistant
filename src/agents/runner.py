from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from crewai import LLM
from haystack.dataclasses import Document

from pathlib import Path
from datetime import datetime
import json

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from ..eval.guardrails import GuardrailsWrapper
from ..eval.trulens import TruLensMonitor
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

    def save_output(self, result: CrewResult, output_base_dir: Path = None) -> dict[str, Path]:
        """
        Save crew output to organized subdirectories in outputs/.
        
        Structure:
        outputs/
        ├── md/YYYYMMDD_HHMMSS_topic/summary.md
        ├── json/YYYYMMDD_HHMMSS_topic/summary.json
        ├── txt/YYYYMMDD_HHMMSS_topic/summary.txt
        └── pdf/YYYYMMDD_HHMMSS_topic/summary.pdf
        
        Args:
            result: CrewResult from crew execution
            output_base_dir: Base output directory (default: outputs/)
            
        Returns:
            Dictionary with paths to saved files
        """
        if output_base_dir is None:
            output_base_dir = Path(__file__).resolve().parents[3] / "outputs"
        
        # Create timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = result.topic[:50].replace(" ", "_").replace("/", "-").replace("\\", "-")
        run_name = f"{timestamp}_{topic_slug}"
        
        saved_files = {}
        
        # Common header for all formats
        header_lines = [
            f"Topic: {result.topic}",
            f"Language: {result.language}",
            f"Generated: {timestamp}",
            f"Number of sources: {len(result.context_docs)}",
        ]
        
        # 1. Save as Markdown
        md_dir = output_base_dir / "md" / run_name
        md_dir.mkdir(parents=True, exist_ok=True)
        md_path = md_dir / "summary.md"
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {result.topic}\n\n")
            for line in header_lines:
                f.write(f"**{line.split(':')[0]}**: {':'.join(line.split(':')[1:]).strip()}\n")
            f.write("\n---\n\n")
            f.write(result.final_output)
            
            # Add source documents section
            if result.context_docs:
                f.write("\n\n---\n\n## Source Documents\n\n")
                for i, doc in enumerate(result.context_docs, 1):
                    source = doc.meta.get("source", "Unknown") if doc.meta else "Unknown"
                    f.write(f"### [{i}] {source}\n\n")
                    preview = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
                    f.write(f"{preview}\n\n")
        
        saved_files["markdown"] = md_path
        logger.info("Saved markdown to: %s", md_path)
        
        # 2. Save as JSON
        json_dir = output_base_dir / "json" / run_name
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / "summary.json"
        
        json_data = {
            "topic": result.topic,
            "language": result.language,
            "timestamp": timestamp,
            "output": result.final_output,
            "metadata": {
                "num_sources": len(result.context_docs),
                "output_length_chars": len(result.final_output),
                "output_length_words": len(result.final_output.split()),
            },
            "source_documents": [
                {
                    "index": i,
                    "source": doc.meta.get("source", "Unknown") if doc.meta else "Unknown",
                    "content_preview": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    "metadata": doc.meta or {}
                }
                for i, doc in enumerate(result.context_docs, 1)
            ]
        }
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        saved_files["json"] = json_path
        logger.info("Saved JSON to: %s", json_path)
        
        # 3. Save as TXT (plain text)
        txt_dir = output_base_dir / "txt" / run_name
        txt_dir.mkdir(parents=True, exist_ok=True)
        txt_path = txt_dir / "summary.txt"
        
        with open(txt_path, "w", encoding="utf-8") as f:
            for line in header_lines:
                f.write(f"{line}\n")
            f.write("=" * 80 + "\n\n")
            f.write(result.final_output)
            
            # Add source documents
            if result.context_docs:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("SOURCE DOCUMENTS\n")
                f.write("=" * 80 + "\n\n")
                for i, doc in enumerate(result.context_docs, 1):
                    source = doc.meta.get("source", "Unknown") if doc.meta else "Unknown"
                    f.write(f"[{i}] {source}\n")
                    f.write("-" * 80 + "\n")
                    preview = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
                    f.write(f"{preview}\n\n")
        
        saved_files["text"] = txt_path
        logger.info("Saved text to: %s", txt_path)
        
        # 4. Save as PDF (simple version using reportlab)
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            
            pdf_dir = output_base_dir / "pdf" / run_name
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / "summary.pdf"
            
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor='#1a1a1a',
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph(result.topic, title_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # Metadata
            meta_style = ParagraphStyle(
                'Metadata',
                parent=styles['Normal'],
                fontSize=10,
                textColor='#666666',
                spaceAfter=6
            )
            for line in header_lines:
                story.append(Paragraph(line, meta_style))
            
            story.append(Spacer(1, 0.3 * inch))
            
            # Main content
            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=11,
                leading=14,
                spaceAfter=12,
                alignment=TA_LEFT
            )
            
            # Split output into paragraphs
            paragraphs = result.final_output.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Handle markdown headers
                    if para.startswith('##'):
                        header_text = para.replace('##', '').strip()
                        story.append(Paragraph(header_text, styles['Heading2']))
                    else:
                        story.append(Paragraph(para, body_style))
            
            # Source documents (if any)
            if result.context_docs:
                story.append(PageBreak())
                story.append(Paragraph("Source Documents", styles['Heading2']))
                story.append(Spacer(1, 0.2 * inch))
                
                source_style = ParagraphStyle(
                    'Source',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=11,
                    leftIndent=20,
                    spaceAfter=15
                )
                
                for i, doc in enumerate(result.context_docs, 1):
                    source = doc.meta.get("source", "Unknown") if doc.meta else "Unknown"
                    story.append(Paragraph(f"<b>[{i}] {source}</b>", styles['Heading3']))
                    preview = doc.content[:400] + "..." if len(doc.content) > 400 else doc.content
                    story.append(Paragraph(preview, source_style))
            
            doc.build(story)
            saved_files["pdf"] = pdf_path
            logger.info("Saved PDF to: %s", pdf_path)
            
        except ImportError:
            logger.warning("reportlab not installed - skipping PDF generation")
            logger.info("Install with: pip install reportlab")
        except Exception as e:
            logger.warning("Failed to generate PDF: %s", e)
        
        logger.info("All outputs saved to subdirectories under: %s", output_base_dir)
        return saved_files
    

def get_crew_runner() -> CrewRunner:
    """Factory function for dependency injection."""
    return CrewRunner()