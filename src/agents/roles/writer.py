from __future__ import annotations

from crewai import Agent


def create_writer_agent(llm) -> Agent:
    """
    Create the Writer agent.
    
    Responsibilities:
    - Draft initial literature summary based on retrieved context
    - Use academic tone and structure
    - Cite sources appropriately
    - Keep summaries concise (5-8 sentences)
    """
    return Agent(
        role="Academic Writer",
        goal="Write a concise, well-structured literature summary on the given topic",
        backstory=(
            "You are an experienced academic writer specializing in literature reviews. "
            "You excel at synthesizing complex information from multiple sources into "
            "clear, coherent summaries. You always maintain academic integrity by "
            "properly citing sources and avoiding speculation."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )