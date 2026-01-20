from __future__ import annotations

from crewai import Task


def create_translator_task(agent, factchecker_task: Task, target_language: str) -> Task:
    """
    Create the translator task.

    Args:
        agent: The Translator agent
        factchecker_task: The previous factchecker task (for context)
        target_language: Target language code (e.g., 'de', 'fr', 'es')
    """
    language_names = {
        'de': 'German',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
    }
    
    lang_name = language_names.get(target_language.lower(), target_language)
    
    description = f"""
Translate the fact-checked text from the previous task to {lang_name}.

Your responsibilities:
- Translate accurately while preserving academic tone
- Keep all citations [1], [2], etc. EXACTLY as they are
- Maintain paragraph structure and formatting
- Ensure the translation reads naturally in {lang_name}
- Do NOT add or remove any information

Your task: Return a high-quality translation that preserves the meaning, tone, and citations.
"""

    return Task(
        description=description,
        expected_output=(
            f"A high-quality translation in {lang_name} that:\n"
            "- Preserves all citations in their original format\n"
            "- Maintains academic tone and style\n"
            "- Reads naturally in the target language\n"
            "- Keeps the same structure and formatting"
        ),
        agent=agent,
        context=[factchecker_task]
    )
