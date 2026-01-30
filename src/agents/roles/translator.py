"""
Translator Agent Role

Creates the Translator agent for multilingual support.
This agent translates summaries while preserving citations and academic tone.
"""
from __future__ import annotations

from crewai import Agent


def create_translator_agent(llm) -> Agent:
    """
    Create the Translator agent.
    
    Responsibilities:
    - Translate summaries to target language
    - Preserve all citations exactly as written
    - Maintain academic tone in target language
    - Do not add or remove information
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured Translator agent
    """
    return Agent(
        role="Academic Translator",
        goal="Translate research summaries while preserving meaning and citations",
        backstory=(
            "You are a professional translator specializing in academic texts. "
            "You maintain the original meaning, preserve citations exactly as they appear, "
            "and adapt the writing style to the target language's academic conventions. "
            "You never modify facts or add interpretations during translation. "
            "Your translations are accurate, natural, and maintain the scholarly tone."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        max_iter=1,
    )