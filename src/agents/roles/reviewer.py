"""
Reviewer Agent Role

Creates the Reviewer agent with text analysis capabilities.
This agent improves clarity and coherence of drafts.
"""
from __future__ import annotations

from crewai import Agent

from ..tools import analyze_text_quality


def create_reviewer_agent(llm) -> Agent:
    """
    Create the Reviewer agent.
    
    The Reviewer agent has access to text analysis tools
    to objectively assess text quality.
    
    Responsibilities:
    - Improve clarity, coherence, and flow
    - Enhance academic writing style
    - Preserve all original claims and citations
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured Reviewer agent
    """
    return Agent(
        role="Academic Reviewer",
        goal="Improve clarity and coherence WITHOUT adding new information",
        backstory=(
            "You are a meticulous peer reviewer with years of experience in academic publishing. "
            "You improve sentence structure, fix grammar, and enhance flow - but you NEVER add new facts. "
            "Your job is to polish, not to expand. You preserve every citation exactly as written. "
            "You understand that adding unsourced information would be academic misconduct. "
            "Your edits are purely stylistic, never substantive."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
        tools=[analyze_text_quality],
    )