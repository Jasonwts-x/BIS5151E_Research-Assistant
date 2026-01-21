from __future__ import annotations

from crewai import Agent


def create_writer_agent(llm) -> Agent:
    """
    Create the Writer agent with strict anti-hallucination constraints.
    """
    return Agent(
        role="Academic Writer",
        goal="Write a concise, factual summary using ONLY the provided context",
        backstory=(
            "You are an experienced academic writer who STRICTLY adheres to source material. "
            "You NEVER invent information, fabricate citations, or add claims not supported by the provided context. "
            "Your core principle: If it's not in the context, you don't write it. "
            "You are praised for accuracy, not creativity. "
            "You understand that making up sources is academic misconduct."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,  # Limit iterations to prevent over-thinking
    )