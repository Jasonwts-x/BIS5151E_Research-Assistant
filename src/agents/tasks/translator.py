from __future__ import annotations

from crewai import Task


def create_translator_task(agent, text: str, target_language: str) -> Task:
    """
    Create the translator task.

    NOTE: This is a placeholder for Step H (DeepL integration).
    Currently not used in the workflow.

    Args:
        agent: The Translator agent
        text: The fact-checked text to translate
        target_language: Target language code (e.g., 'de', 'fr', 'es')
    """
    description = f"""
Translate the following text to {target_language}:

{text}

Your responsibilities:
- Translate accurately while preserving academic tone
- Keep all citations [1], [2], etc. EXACTLY as they are
- Maintain paragraph structure and formatting
- Ensure the translation reads naturally in {target_language}

Your task: Return a high-quality translation that preserves the meaning, tone, and citations.
"""

    return Task(
        description=description,
        expected_output=(
            f"A high-quality translation in {target_language} that:\n"
            "- Preserves all citations in their original format\n"
            "- Maintains academic tone and style\n"
            "- Reads naturally in the target language\n"
            "- Keeps the same structure and formatting"
        ),
        agent=agent,
    )
