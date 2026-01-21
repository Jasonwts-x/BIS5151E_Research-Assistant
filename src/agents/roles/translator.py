from __future__ import annotations

from crewai import Agent


def create_translator_agent(llm) -> Agent:
    """
    Create the Translator agent.
    
    NOTE: Currently used in Step H (future). For now, translation quality issues
    might be due to the fact that the text has already been through multiple agents.
    
    To improve translation quality, consider:
    1. Using the translator earlier in the pipeline (after writer, before reviewer)
    2. Or translating the FINAL verified text (current approach)
    """
    return Agent(
        role="Academic Translator",
        goal="Translate the final summary to the target language while preserving meaning, tone, and ALL citations",
        backstory=(
            "You are a professional academic translator with expertise in maintaining "
            "technical accuracy and academic tone across languages. Your core principle: "
            "preserve the EXACT meaning and ALL citations [1], [2], etc. in their original format. "
            "You focus on natural-sounding translations that read fluently in the target language "
            "while keeping the academic register. You never add or remove information during translation."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
    )