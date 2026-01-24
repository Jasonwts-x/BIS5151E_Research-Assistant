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
        'fr': 'French',
        'es': 'Spanish',
        'it': 'Italian',
        'pt': 'Portuguese',
        'nl': 'Dutch',
        'pl': 'Polish',
        'ru': 'Russian',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ko': 'Korean',
    }
    
    language_name = language_names.get(target_language.lower(), target_language)
    
    description = f"""
    Translate the fact-checked text from the previous task to {language_name}.
  
    ⚠️ CRITICAL TRANSLATION RULES:
    1. Preserve ALL citations exactly as they appear: [1], [2], [3], etc.
    2. Maintain academic tone appropriate for {language_name}
    3. Keep the same meaning and structure
    4. Do NOT add or remove information
    5. Do NOT modify, remove, or relocate citations
    6. Translate the "## References" section header but keep source names unchanged

    IMPORTANT:
    - Citations like [1], [2] must appear in the EXACT same positions
    - Academic terminology should use standard {language_name} conventions
    - If a technical term has no direct translation, use the English term in italics

    Your task: Provide a faithful {language_name} translation that preserves 
    all content, structure, and citations from the original.
    """

    return Task(
        description=description,
        expected_output=(
            f"A complete {language_name} translation of the fact-checked summary. "
            "All citations [1], [2], etc. must be preserved in their exact positions. "
            "Academic tone and terminology appropriate for the target language. "
            "No content added or removed."
        ),
        agent=agent,
        context=[factchecker_task]
    )