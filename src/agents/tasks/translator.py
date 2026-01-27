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
   
    language_name = language_names.get(target_language.lower(), target_language)
    ref_header = reference_headers.get(target_language.lower(), 'References')
   
    description = f"""
Translate the fact-checked text from the previous task to {language_name}.
 
⚠️ CRITICAL TRANSLATION RULES:
 
1. **Preserve ALL citations exactly**: [1], [2], [3], etc. in the EXACT same positions
2. **Maintain academic tone** appropriate for {language_name}
3. **Keep the same meaning and structure** - do NOT add or remove information
4. **Do NOT modify citations** - they must stay exactly as [1], [2], [3]
5. **Translate the References header** to "{ref_header}" but keep source details unchanged
6. **Technical terms**: Use standard {language_name} academic conventions
 
⚠️ CRITICAL OUTPUT INSTRUCTION:
You MUST return the COMPLETE TRANSLATED TEXT only.
 
DO NOT return:
- ❌ "Here is the translation: ..."
- ❌ "I have translated the text to {language_name}: ..."
- ❌ "The {language_name} version is: ..."
- ❌ Any meta-commentary about the translation
 
DO return:
- ✅ The actual translated summary text with citations
- ✅ The translated ## {ref_header} section
- ✅ Nothing else
 
CORRECT OUTPUT FORMAT (Example for German):
 
Maschinelles Lernen ist eine Teilmenge der künstlichen Intelligenz [1]. Es ermöglicht Systemen, aus Daten zu lernen [1][2].
Deep Learning nutzt neuronale Netze [2][3].
 
## {ref_header}
[1] Author, A. (Year). Title of Paper. arXiv preprint arXiv:1234.5678.
[2] Author, B. (Year). Another Paper Title. Source.
[3] Author, C. (Year). Third Paper. Source.
 
INCORRECT OUTPUT:
"Here is the German translation: Maschinelles Lernen ist..."
 
TRANSLATION GUIDELINES:
- Academic terminology: Use established {language_name} equivalents
- If no direct translation exists: Use English term in italics (*machine learning*)
- Citations [N]: Keep in exact same position as original
- Author names: Keep unchanged in References section
- Paper titles: Keep in original language (usually English)
 
Remember: Return ONLY the translated text, not a description of what you did.
"""
 
    return Task(
        description=description,
        expected_output=(
            f"The complete {language_name} translation of the fact-checked summary. "
            f"All citations [1], [2], etc. preserved in exact positions. "
            f"References section header translated to '## {ref_header}'. "
            "Academic tone and terminology appropriate for the target language. "
            "NO meta-commentary - ONLY the translated text."
        ),
        agent=agent,
        context=[factchecker_task]
    )
