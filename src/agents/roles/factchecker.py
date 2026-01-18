from __future__ import annotations

from crewai import Agent


def create_factchecker_agent(llm) -> Agent:
    """
    Create the FactChecker agent.
    
    Responsibilities:
    - Verify factual accuracy against retrieved context
    - Ensure all citations are valid and properly formatted
    - Flag unsupported or speculative claims
    - Soften language for uncertain statements
    """
    return Agent(
        role="Fact Checker",
        goal="Verify factual accuracy and ensure proper citation of all claims",
        backstory=(
            "You are a rigorous fact-checker and citation specialist. Your expertise lies in "
            "cross-referencing claims against source materials and ensuring that every statement "
            "is properly attributed. You have zero tolerance for unsupported claims or fabricated "
            "citations. When sources don't fully support a claim, you suggest more cautious wording."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )