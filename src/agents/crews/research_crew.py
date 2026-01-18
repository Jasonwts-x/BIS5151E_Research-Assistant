from __future__ import annotations

import logging

from crewai import Crew, Process

from ..roles import (
    create_factchecker_agent,
    create_reviewer_agent,
    create_writer_agent,
)
from ..tasks import (
    create_factchecker_task,
    create_reviewer_task,
    create_writer_task,
)

logger = logging.getLogger(__name__)


class ResearchCrew:
    """
    Research Assistant Crew composition.
    
    Orchestrates Writer → Reviewer → FactChecker pipeline using CrewAI.
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
        logger.info("ResearchCrew agents initialized successfully")

    def run(self, topic: str, context: str) -> str:
        """
        Execute the research crew workflow.
        
        Args:
            topic: Research topic/question
            context: Retrieved context from RAG pipeline
            
        Returns:
            Final fact-checked summary
        """
        logger.info("Starting ResearchCrew workflow for topic: %s", topic)
        
        # Create tasks with current inputs
        writer_task = create_writer_task(self.writer, topic, context)
        reviewer_task = create_reviewer_task(self.reviewer, draft="{previous_output}")
        factchecker_task = create_factchecker_task(
            self.factchecker,
            text="{previous_output}",
            context=context,
        )
        
        # Create crew with sequential process
        crew = Crew(
            agents=[self.writer, self.reviewer, self.factchecker],
            tasks=[writer_task, reviewer_task, factchecker_task],
            process=Process.sequential,
            verbose=True,
        )
        
        # Execute and return final output
        logger.info("Executing crew workflow (sequential process)")
        result = crew.kickoff()
        logger.info("Crew workflow completed successfully")
        
        # CrewAI returns a CrewOutput object; get the final task output
        return str(result)


# ============================================================================
# TODO (Step F): Add agent memory support
# ============================================================================