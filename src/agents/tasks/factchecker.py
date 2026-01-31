"""FactChecker Task Definition"""
from crewai import Task
 
 
def create_factchecker_task(agent, reviewer_task, context: str) -> Task:
    """Create fact-checking task with strict output rules."""

    description = f"""
        
TASK: VERIFY every claim in the text matches text against sources. 
REMOVE unsupported claims. ADD References section.

SOURCES:
{context}

ACTIONS:
1. Verify every claim has an inline citation ([1], [2], etc.).
2. Cross-check each claim against the corresponding source in the SOURCES.
3. Remove any unsupported claims.
4. Create a "## References" section at the end with ALL cited sources.
5. Format each reference in APA7 style.

REQUIREMENTS:
1. Every citation [n] must match source [n] in the SOURCES.
2. Only remove unsupported claims or fix citation mismatches.
3. Maintain original meaning and tone of the text.
4. Output properly cited text exactly as is.
5. Start directly with summary text (no preamble). Don't include meta-commentary.
6. Use title case (not ALL CAPS) for titles.

APA7 FORMAT:
[1] Author, A. B. (Year). Paper title. Journal/Source.

For arXiv: [1] Author, A. (Year). Title. arXiv:XXXX.XXXXX.
For unknown: [1] Unknown. (n.d.). [Filename].

CRITICAL: You MUST create the ## References section. This is mandatory.


OUTPUT STRUCTURE:
[Summary text with citations [1], [2], etc.]

## References
[1] First source in APA7 format.
[2] Second source in APA7 format.
[3] Third source in APA7 format.

"""
    
    expected_output = f"""
        
Fact-checked text with verified claims. 
All claims verified against sources.
MUST include ## References section with APA7 citations.
Format: Summary text, then blank line, then ## References, then list of sources.

"""
    
    context = [reviewer_task]

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context
    )