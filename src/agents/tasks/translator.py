"""Translator Task Definition"""
from crewai import Task
 
 
def create_translator_task(agent, factchecker_task: Task, target_language: str) -> Task:
    """Create translator task with minimal necessary instructions."""
    
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
   
    reference_headers = {
        'de': 'Literaturverzeichnis',
        'fr': 'Références',
        'es': 'Referencias',
        'it': 'Riferimenti',
        'pt': 'Referências',
        'nl': 'Referenties',
        'pl': 'Bibliografia',
        'ru': 'Список литературы',
        'ja': '参考文献',
        'zh': '参考文献',
        'ko': '참고문헌',
    }
   
    language = language_names.get(target_language.lower(), target_language)
    reference_header = reference_headers.get(target_language.lower(), 'References')
   
    description = f"""
    
TASK: Translate the fact-checked text from the previous task to {language}.

PRESERVE:
- All citations ([1], [2], etc.) in exact positions.
- All factual content. Maintain original meaning and structure.
- Academic tone appropriate for {language}.

TRANSLATE:
- Main text to natural {language}.
- Use standard academic terminology in {language}.
- If there is no direct translation, use the English term in quotation marks.
- "References" section header to "{reference_header}".
    
KEEP UNCHANGED:
- Citation details in the References section.
- Author names, publication years, and source titles.

OUTPUT FORMAT:
- Begin directly with the translated text.
- Do not include meta-commentary like "Here is the translation...".
- End with "{reference_header}" section.
 
"""
 
    expected_output= f"""T
    
The complete {language} translation of the fact-checked summary 
with academic tone and terminology appropriate for the target language. 
All citations ([1], [2], etc.) preserved in exact positions and not meta-commentary.
        
"""

    context=[factchecker_task]

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context
    )