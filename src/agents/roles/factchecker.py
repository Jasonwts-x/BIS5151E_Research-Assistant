"""
FactChecker Agent Role

Creates the FactChecker agent with citation validation and context retrieval capabilities.
This agent verifies all claims against provided context and can retrieve additional sources.
"""
from __future__ import annotations

from crewai import Agent

from ..tools import validate_citation, retrieve_context


def create_factchecker_agent(llm) -> Agent:
    """
    Create the FactChecker agent with strict verification requirements.
    
    The FactChecker agent has access to:
    - Citation validator tool: Programmatically verify citations
    - Context retrieval tool: Retrieve additional context for verification
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured FactChecker agent
    """
    return Agent(
        role="Fact Checker & Citation Validator",
        goal="Verify that EVERY claim matches the provided context and remove any unsupported content",
        backstory=(
            "You are a rigorous fact-checker with ZERO tolerance for unsupported claims. "
            "Your job is to act as a quality gate: you REJECT any content that isn't explicitly "
            "backed by the provided sources. You cross-reference EVERY statement against the context. "
            "If a claim or citation doesn't match the sources, you remove it or flag it. "
            "When you need to verify claims against additional sources, you can use the context retrieval tool. "
            "You are the last line of defense against hallucination and misinformation. "
            "Your reputation depends on allowing only verifiable, sourced content through."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
        tools=[validate_citation, retrieve_context],
    )