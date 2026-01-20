from __future__ import annotations

from crewai import Agent


def create_translator_agent(llm) -> Agent:
    """
    Create the Translator agent.
    
    NOTE: This is a placeholder for Step H (DeepL integration).
    Currently not used in the workflow.
    
    Future responsibilities:
    - Translate final output to target language
    - Preserve citations and formatting
    - Maintain academic tone in target language
    """
    return Agent(
        role="Academic Translator",
        goal="Translate the final summary to the target language while preserving meaning and citations",
        backstory=(
            "You are a professional academic translator with expertise in maintaining "
            "technical accuracy and academic tone across languages. You preserve all "
            "citations and formatting while ensuring natural-sounding translations."
        ),
        verbose=True,           # TODO: Use True during development, switch to False for production
        allow_delegation=False,
        llm=llm,
    )