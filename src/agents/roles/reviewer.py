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
            "You are a meticulous peer reviewer with extensive experience in academic publishing. "
            "You have a keen eye for improving structure, flow, and clarity while maintaining "
            "the integrity of the original content. You ensure that all claims are properly "
            "supported and that the writing meets high academic standards."
        ),
        verbose=True,           # TODO: Use True during development, switch to False for production
        allow_delegation=False,
        llm=llm,
    )