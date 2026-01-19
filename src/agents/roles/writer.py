from __future__ import annotations

from crewai import Agent


def create_writer_agent(llm) -> Agent:
    """Create the Writer agent - optimized for speed."""
    return Agent(
        role="Writer",
        goal="Write 300 words summary",
        backstory="You write concise academic summaries. Use only given context.",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,  # WICHTIG: Nur 1 Iteration!
    )
