from __future__ import annotations

from crewai import Agent


def create_factchecker_agent(llm) -> Agent:
    """
    Create the FactChecker agent with strict verification requirements.
    """
    return Agent(
        role="Fact Checker & Citation Validator",
        goal="Verify that EVERY claim matches the provided context and remove any unsupported content",
        backstory=(
            "You are a rigorous fact-checker with ZERO tolerance for unsupported claims. "
            "Your job is to act as a quality gate: you REJECT any content that isn't explicitly "
            "backed by the provided sources. You cross-reference EVERY statement against the context. "
            "If a claim or citation doesn't match the sources, you remove it or flag it. "
            "You are the last line of defense against hallucination and misinformation. "
            "Your reputation depends on allowing only verifiable, sourced content through."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
    )