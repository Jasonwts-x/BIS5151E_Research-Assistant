from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from crewai import Crew, Process

if TYPE_CHECKING:
    from crewai import Agent, Task

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

        Args:
            topic: Research topic/question
            context: Retrieved context from RAG pipeline
            language: Target language ('en', 'de', 'es', 'fr')

        Returns:
            Final summary (translated if language != 'en')
        """
        logger.info(
            "Starting ResearchCrew workflow for topic: %s (language: %s)", topic, language)

        # Create base tasks with proper context chaining
        writer_task = create_writer_task(self.writer, topic, context)
        reviewer_task = create_reviewer_task(self.reviewer, writer_task)
        factchecker_task = create_factchecker_task(
            self.factchecker,
            reviewer_task,
            context,
        )

        # Base agents and tasks - use list() to satisfy type checker
        agents: list = [self.writer, self.reviewer, self.factchecker]
        tasks: list = [writer_task, reviewer_task, factchecker_task]

        # Add translator if language is not English
        if language.lower() != "en":
            logger.info("Adding translator for language: %s", language)
            translator_task = create_translator_task(
                self.translator,
                factchecker_task,
                language
            )
            agents.append(self.translator)
            tasks.append(translator_task)

        # Create crew with sequential process
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

        # Execute and return final output
        logger.info("Executing crew workflow with %d agents", len(agents))
        result = crew.kickoff()
        logger.info("Crew workflow completed successfully")

        # CrewAI returns a CrewOutput object; get the final task output
        return str(result)


# ============================================================================
# TODO (Step F): Add agent memory support
# ============================================================================
