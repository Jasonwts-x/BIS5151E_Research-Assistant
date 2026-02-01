"""
Writer Agent Role.

Creates the Writer agent with context retrieval capabilities.
This agent drafts initial summaries from provided or dynamically retrieved context.

Architecture:
    Writer is the first agent in the pipeline.
    Has access to retrieve_context tool for dynamic document retrieval.
"""
from __future__ import annotations

from crewai import Agent

from ..tools import retrieve_context


def create_writer_agent(llm) -> Agent:
    """
    Create the Writer agent with strict anti-hallucination constraints.
    
    The Writer agent has access to the context retrieval tool, allowing it to
    search the knowledge base for additional information when needed.
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured Writer agent with context retrieval capability
    """
    return Agent(
        role="Academic Writer",
        goal="Write clear, concise, well-cited research summaries based strictly on provided sources",
        backstory=(
            "You are an experienced academic writer who specializes in synthesizing research literature. "
            "Your fundamental principle is strict adherence to source material - you never invent information, "
            "fabricate citations, or make claims without explicit source support. If information is not in the "
            "provided sources, you do not include it. You cite all factual claims using [1], [2], etc. notation "
            "and understand that academic integrity depends on accurate attribution. When initial context is "
            "insufficient, you can search the knowledge base for additional relevant information."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
        max_execution_time=600,
        tools=[retrieve_context],
    )