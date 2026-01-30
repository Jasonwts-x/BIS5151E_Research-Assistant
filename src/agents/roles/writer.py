"""
Writer Agent Role

Creates the Writer agent with context retrieval capabilities.
This agent drafts initial summaries from provided or dynamically retrieved context.
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
        goal="Write clear, concise, well-cited research summaries",
        backstory=(
            "You are an experienced academic writer who STRICTLY adheres to source material. "
            "You NEVER invent information, fabricate citations, or add claims not supported by sources. "
            "Your core principle: If it's not in the sources, you don't write it. "
            "When the provided context is insufficient, you can use the context retrieval tool "
            "to search for additional information from the knowledge base. "
            "You always cite your sources properly using [1], [2], etc. notation. "
            "You understand that making up sources is academic misconduct."
            "You are praised for accuracy and thoroughness, not creativity."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
        tools=[retrieve_context],
    )