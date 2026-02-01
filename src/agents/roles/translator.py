"""
Translator Agent Role.

Creates the Translator agent for multilingual support.
This agent translates summaries while preserving citations and academic tone.

Architecture:
    Translator is an optional fourth agent (only used when language != "en").
"""
from __future__ import annotations

from crewai import Agent


def create_translator_agent(llm) -> Agent:
    """
    Create the Translator agent.
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured Translator agent
    """
    return Agent(
        role="Academic Translator",
        goal="Translate research summaries accurately while preserving all citations and academic tone",
        backstory=(
            "You are a professional translator specializing in academic and technical content. "
            "Your translations maintain the precise meaning of the original text while adapting "
            "the writing style to the target language's academic conventions. You preserve all "
            "citations [1], [2], etc. in their exact original positions and never modify factual "
            "content or add interpretations. Your translations are both linguistically accurate and "
            "stylistically appropriate for academic discourse in the target language."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
    )