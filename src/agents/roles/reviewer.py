from __future__ import annotations

from crewai import Agent


def create_reviewer_agent(llm) -> Agent:
    """
    Create the Reviewer agent.

    Responsibilities:
    - Review and improve draft clarity, coherence, and flow
    - Ensure academic writing standards
    - Preserve factual claims and citations
    - Enhance readability without changing meaning
    """
    return Agent(
        role="Academic Reviewer",
        goal="Improve the clarity, coherence, and academic quality of the draft",
        backstory=(
            "You improve text quality. Keep facts unchanged."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
    )
