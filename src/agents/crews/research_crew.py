from __future__ import annotations
 
import logging
from typing import TYPE_CHECKING
 
from crewai import Agent, Crew, Process, Task
 
from ..roles import (
    create_factchecker_agent,
    create_reviewer_agent,
    create_translator_agent,
    create_writer_agent,
)
 
from ..tasks import (
    create_factchecker_task,
    create_reviewer_task,
    create_translator_task,
    create_writer_task,
)
 
logger = logging.getLogger(__name__)
 
 
class ResearchCrew:
    """
    Research Assistant Crew composition.
 
    Orchestrates Writer → Reviewer → FactChecker → (Translator) pipeline using CrewAI.
    Supports both strict mode (with context) and fallback mode (without context).
    """
 
    def __init__(self, llm):
        """
        Initialize the crew with agents.
 
        Args:
            llm: Language model instance (from Ollama via LangChain)
        """
        self.llm = llm
 
        # Initialize agents
        logger.info("Initializing ResearchCrew agents")
        self.writer = create_writer_agent(llm)
        self.reviewer = create_reviewer_agent(llm)
        self.factchecker = create_factchecker_agent(llm)
        self.translator = create_translator_agent(llm)
        logger.info("ResearchCrew agents initialized successfully")
 
    def run(self, topic: str, context: str, language: str = "en") -> str:
        """
        Execute the research crew workflow.
       
        Detects whether context is available and adjusts workflow accordingly:
        - WITH context: Full pipeline (Writer → Reviewer → FactChecker)
        - WITHOUT context: Simplified pipeline (Writer only, general knowledge mode)
 
        Args:
            topic: Research topic/question
            context: Retrieved RAG context (may be empty/unavailable message)
            language: Target language
 
        Returns:
            Final output string
        """
        logger.info("Starting crew run for topic: %s", topic)
 
        # Detect if we have actual context or not
        has_context = self._has_valid_context(context)
 
        if not has_context:
            logger.warning("No valid context available - using fallback mode")
            return self._run_fallback_mode(topic, language)
        else:
            logger.info("Valid context available - using strict mode with %d chars", len(context))
            return self._run_strict_mode(topic, context, language)
 
    def _has_valid_context(self, context: str) -> bool:
        """
        Check if context contains actual documents or is just a placeholder.
       
        Args:
            context: Context string from RAG retrieval
           
        Returns:
            True if valid context exists, False otherwise
        """
        if not context:
            return False
       
        # Check for common "no context" indicators
        no_context_indicators = [
            "⚠️ NO CONTEXT AVAILABLE ⚠️",
            "NO CONTEXT AVAILABLE",
            "No context available",
            "No documents were retrieved",
        ]
       
        for indicator in no_context_indicators:
            if indicator in context:
                logger.debug("Context validation failed: contains '%s'", indicator)
                return False
       
        # Check if context is too short (likely just a message)
        if len(context.strip()) < 100:
            logger.debug("Context validation failed: too short (%d chars)", len(context.strip()))
            return False
       
        # Check if context contains source markers (indicating real documents)
        if "SOURCE" not in context:
            logger.debug("Context validation failed: no SOURCE markers found")
            return False
       
        logger.debug("Context validation passed: %d chars with SOURCE markers", len(context))
        return True
 
    def _run_strict_mode(self, topic: str, context: str, language: str) -> str:
        """
        Run full pipeline with strict fact-checking against provided context.
       
        Pipeline: Writer → Reviewer → FactChecker → (Translator if needed)
 
        Args:
            topic: Research topic
            context: Retrieved context
            language: Target language
           
        Returns:
            Fact-checked output with citations and references
        """
        logger.info("Running STRICT MODE - will verify all claims against context")
       
        # Create tasks
        writer_task = create_writer_task(
            agent=self.writer,
            topic=topic,
            context=context,
            mode="strict"
        )
       
        reviewer_task = create_reviewer_task(
            agent=self.reviewer,
            writer_task=writer_task
        )
       
        factchecker_task = create_factchecker_task(
            agent=self.factchecker,
            reviewer_task=reviewer_task,
            context=context
        )
       
        # Build crew
        tasks = [writer_task, reviewer_task, factchecker_task]
       
        # Add translation if needed (future enhancement)
        if language != "en":
            logger.warning("Translation not yet implemented, using English")
       
        crew = Crew(
            agents=[self.writer, self.reviewer, self.factchecker],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
       
        # Execute
        logger.info("Executing crew with %d tasks", len(tasks))
        result = crew.kickoff()
 
        formatted_output = self._format_output(result, mode="strict")
       
        logger.info("Crew execution completed. Output length: %d chars", len(formatted_output))
        return formatted_output
   
    def _run_fallback_mode(self, topic: str, language: str) -> str:
        """
        Run full pipeline using general knowledge (no local database context).
       
        Pipeline: Writer → Reviewer → FactChecker → (Translator if needed)
       
        The agents will:
        1. Writer: Use general academic knowledge with cautious language
        2. Reviewer: Check clarity, coherence, and academic tone
        3. FactChecker: Verify claims are reasonable and properly qualified
       
        Args:
            topic: Research topic
            language: Target language
           
        Returns:
            Reviewed and fact-checked summary based on general knowledge
        """
        logger.info("Running FALLBACK MODE - using general knowledge")
       
        # Create fallback writer task
        writer_task = create_writer_task(
            agent=self.writer,
            topic=topic,
            context="",
            mode="fallback"
        )
 
        reviewer_task = create_reviewer_task(
            agent=self.reviewer,
            writer_task=writer_task
        )
       
        factchecker_task = create_factchecker_task(
            agent=self.factchecker,
            reviewer_task=reviewer_task,
            context=""
        )
 
        tasks = [writer_task, reviewer_task, factchecker_task]
 
        if language != "en":
            logger.warning("Translation not yet implemented, using English")
 
        crew = Crew(
            agents=[self.writer, self.reviewer, self.factchecker],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
       
        # Execute
        logger.info("Executing fallback crew with %d tasks", len(tasks))
        result = crew.kickoff()
 
        formatted_output = self._format_output(result, mode="fallback")
 
        logger.info("Fallback crew execution completed. Output length: %d chars", len(formatted_output))
        return formatted_output
 
    def _format_output(self, result, mode: str = "strict") -> str:
        """
        Format crew output correctly, preserving citations and references.
       
        Args:
            result: CrewAI task result
            mode: "strict" or "fallback"
           
        Returns:
            Formatted output with citations and references
        """
        logger.debug("Formatting output (mode: %s, result type: %s)", mode, type(result))
       
        try:
            # Extract raw text output from CrewAI result
            if hasattr(result, 'raw'):
                output_text = str(result.raw)
                logger.debug("Using result.raw")
            elif hasattr(result, 'output'):
                output_text = str(result.output)
                logger.debug("Using result.output")
            else:
                output_text = str(result)
                logger.debug("Using str(result)")
           
            # Clean up the output
            output_text = output_text.strip()
           
            # Log statistics
            citation_count = self._extract_citations_count(output_text)
            has_references = "## References" in output_text or "## Literaturverzeichnis" in output_text
           
            logger.info(
                "✅ Output formatted: %d chars, %d citations, has_references=%s",
                len(output_text),
                citation_count,
                has_references
            )
           
            # Validation: Warn if no citations in strict mode
            if mode == "strict" and citation_count == 0:
                logger.warning("⚠️ STRICT MODE but no citations [1], [2] found in output!")
           
            # Validation: Warn if no references section in strict mode
            if mode == "strict" and not has_references:
                logger.warning("⚠️ STRICT MODE but no ## References section found!")
           
            return output_text
           
        except Exception as e:
            logger.error("❌ Error formatting output: %s. Using fallback.", e, exc_info=True)
            return str(result)
   
    def _extract_citations_count(self, text: str) -> int:
        """
        Count inline citations in text for debugging.
       
        Args:
            text: Text to analyze
           
        Returns:
            Number of citations found (e.g., [1], [2], etc.)
        """
        import re
        citations = re.findall(r'\[\d+\]', text)
        return len(citations)


# ============================================================================
# TODO (Step F): Add agent memory support
# ============================================================================