"""
FactChecker Agent Role.

Creates the FactChecker agent with citation validation and context retrieval capabilities.
This agent verifies all claims against provided context and can retrieve additional sources.

Architecture:
    FactChecker is the third agent in the pipeline.
    Has access to validate_citation and retrieve_context tools.
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
        role="Academic Fact Checker & Citation Validator",
        goal="Verify every claim against the provided sources, remove any unsupported content",
        backstory=(
            "You are a rigorous fact-checker who serves as the final quality gate for academic content. "
            "You maintain ZERO tolerance for unsupported claims and cross-reference every statement against "
            "the provided source context. When claims lack source support, you remove them or suggest "
            "appropriate hedging language. You validate that all citations [1], [2], etc. correctly "
            "correspond to sources and that the cited content accurately reflects what the source states. "
            "When verification requires additional context, you can retrieve relevant sources from the "
            "knowledge base. You MUST reate a ## References section in APA7 format for all cited sources. "
            "Each reference must use the METADATA from the sources to format properly. "
            "Your role is critical in preventing hallucinations and ensuring that only "
            "verifiable, properly attributed content reaches the final output."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
        max_execution_time=600,
        tools=[validate_citation, retrieve_context],
    )