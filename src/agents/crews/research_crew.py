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
            language: Target language (only 'en' currently supported)

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
            logger.info("Valid context available - using strict mode")
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
            "NO CONTEXT AVAILABLE",
            "No context available",
            "No documents were retrieved",
            "⚠️",
        ]
        
        for indicator in no_context_indicators:
            if indicator in context:
                return False
        
        # Check if context is too short (likely just a message)
        if len(context.strip()) < 100:
            return False
        
        # Check if context contains source markers (indicating real documents)
        if "SOURCE [" not in context:
            return False
        
        return True

    def _run_strict_mode(self, topic: str, context: str, language: str) -> str:
        """
        Run full pipeline with strict fact-checking against provided context.
        
        Args:
            topic: Research topic
            context: Retrieved context (guaranteed to be valid)
            language: Target language
            
        Returns:
            Fact-checked output
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
        
        # Add translation if needed (future)
        if language != "en":
            logger.warning("Translation not yet implemented, using English")
        
        crew = Crew(
            agents=[self.writer, self.reviewer, self.factchecker],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
        
        # Execute
        result = crew.kickoff()
        
        return str(result)
    
    def _run_fallback_mode(self, topic: str, language: str) -> str:
        """
        Run simplified pipeline using general knowledge (no fact-checking).
        
        Args:
            topic: Research topic
            language: Target language
            
        Returns:
            General knowledge summary
        """
        logger.info("Running FALLBACK MODE - using general knowledge")
        
        # Create fallback writer task
        writer_task = create_writer_task(
            agent=self.writer,
            topic=topic,
            context="",  # Empty context
            mode="fallback"
        )
        
        # Build simplified crew (writer only)
        crew = Crew(
            agents=[self.writer],
            tasks=[writer_task],
            process=Process.sequential,
            verbose=True,
        )
        
        # Execute
        result = crew.kickoff()
        
        return str(result)    


# ============================================================================
# TODO (Step F): Add agent memory support
# ============================================================================