"""
Reviewer Agent Role.

Creates the Reviewer agent with text analysis capabilities.
This agent improves clarity and coherence of drafts.

Architecture:
    Reviewer is the second agent in the pipeline.
    Has access to analyze_text_quality tool for objective assessment.
"""
from __future__ import annotations

from crewai import Agent

from ..tools import analyze_text_quality


def create_reviewer_agent(llm) -> Agent:
    """
    Create the Reviewer agent.
    
    The Reviewer agent has access to text analysis tools to objectively assess text quality.
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured Reviewer agent
    """
    return Agent(
        role="Academic Reviewer",
        goal="Improve clarity and readability while preserving all factual content and citations",
        backstory=(
            "You are a meticulous peer reviewer with expertise in academic publishing. "
            "Your role is to enhance the quality of academic writing through improved sentence structure, "
            "better grammar, and clearer flow of ideas. However, you operate under strict constraints: "
            "you improve style and presentation but never add new factual claims or remove existing citations. "
            "Your edits are purely stylistic and linguistic - you polish the text without changing its "
            "substantive content. You understand that adding unsourced information would compromise academic integrity."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
        tools=[analyze_text_quality],
    )