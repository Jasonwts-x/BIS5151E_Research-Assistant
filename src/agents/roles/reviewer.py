from __future__ import annotations

from crewai import Agent


def create_reviewer_agent(llm) -> Agent:
    """
    Create the Reviewer agent.

    Responsibilities:
    - Improve clarity, coherence, and flow
    - Enhance academic writing style
    - Preserve all original claims and citations
    """
    return Agent(
        role="Academic Reviewer",
        goal="Improve clarity, coherence, and academic quality of drafts",
        backstory=(
            "You are a meticulous peer reviewer with years of experience in academic "
            "publishing. You identify gaps in logic, improve sentence structure, and "
            "ensure arguments flow naturally. You preserve the original meaning while "
            "enhancing readability. You never add new claims without supporting evidence."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
    )