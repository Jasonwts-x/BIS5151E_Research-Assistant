"""
Reviewer Task Definition.

Defines the review task with instructions for improving draft quality.

Architecture:
    Task depends on writer_task output via context parameter.
"""
from __future__ import annotations

from crewai import Task


def create_reviewer_task(agent, writer_task) -> Task:
    """
    Create reviewer task.
    
    Args:
        agent: Reviewer agent instance
        writer_task: Completed writer task (provides context)
        
    Returns:
        Configured Task instance
    """

    description = f"""

TASK: REVIEW and IMPROVE the draft text.

IMPROVE:
- Sentence structure and grammar
- Flow and clarity
- Academic tone

PRESERVE:
- All citations [1], [2], etc.
- All factual claims
- Original meaning

INSTRUCTIONS:
- Enhance readability and coherence.
- Maintain academic style.
- Keep all original references intact.
- Do NOT add meta-commentary about the text itself.
- Do NOT mention what the text "includes" or "contains".

FORBIDDEN PHRASES:
- "This analysis includes..."
- "The text contains..."
- "A references section..."
- "Citations are formatted..."

REMOVE: Any LaTeX notation (\\(x\\), $t$, etc.)


OUTPUT: The improved text ONLY, without any commentary about the text.

"""
    
    expected_output = f"""

Improved draft with enhanced clarity and polished academic style. 
All original citations preserved. No LaTeX notation. NO meta-commentary.

"""
    
    context = [writer_task]

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context
    )