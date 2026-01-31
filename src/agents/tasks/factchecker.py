"""FactChecker Task Definition"""
from crewai import Task
 
 
def create_factchecker_task(agent, reviewer_task, context: str) -> Task:
    """Create fact-checking task with strict output rules."""

    description = f"""
        
TASK: Verify every claim in the text matches text against sources. Remove unsupported claims.

ACTIONS:
1. Verify every claim has an inline citation ([1], [2], etc.).
2. Cross-check each claim against the corresponding source in the context.
3. Remove any unsupported claims.
4. Create a "References" section at the end which includes all cited sources.
5. Format citations in APA7 style.

REQUIREMENTS:
1. Every citation [N] must match source [N] in context below.
2. Only remove unsupported claims or fix citation mismatches.
3. Output properly cited text exactly as is.
4. Maintain original meaning and tone of the text.
5. Start directly with summary text. Don't include meta-commentary.
6. Use the "METADATA" line from the context to format the reference in APA7 style.
7. If metadata incomplete, use filename as title.
8. Use title case (not ALL CAPS) for titles.

APA7 FORMAT:
[1] Author, A. B. (Year). Paper title. Journal/Source.

For arXiv: [1] Author, A. (Year). Title. arXiv:XXXX.XXXXX.
For unknown: [1] Unknown. (n.d.). [Filename].

SOURCES:
{context}

"""
    
    expected_output = f"""
        
Fact-checked text. All claims verified against sources. 
Citations accurate. References section included.

"""
    
    context = [reviewer_task]

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context
    )