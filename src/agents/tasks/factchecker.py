"""
FactChecker Task Definition.

Defines the fact-checking task with strict verification requirements.

Architecture:
    Task depends on reviewer_task output and original context for verification.
"""
from __future__ import annotations

from crewai import Task


def create_factchecker_task(agent, reviewer_task, context: str) -> Task:
    """
    Create fact-checking task with strict output rules.
    
    Args:
        agent: FactChecker agent instance
        reviewer_task: Completed reviewer task (provides text to check)
        context: Original retrieved context for verification
        
    Returns:
        Configured Task instance
    """

    description = f"""
        
TASK: VERIFY every citation in the text matches a source. 
REMOVE unsupported claims. ADD References section.

SOURCES:
{context}

STEPS:
1. Check that every citation [1], [2], etc. matches a source in SOURCES.
2. Remove any unsupported claims that lack citations.
3. Add a "## References" section at the end with ALL cited sources.

APA7 FORMAT:
[1] Author, A. B. (Year). Paper title. Journal/Source.

For arXiv: [1] Author, A. (Year). Title. arXiv:XXXX.XXXXX.
For unknown: [1] Unknown. (n.d.). [Filename].


CRITICAL RULES:
- Start output directly with the summary text (no preamble).
- Every citation [n] must correspond to SOURCE [n] from above.
- Remove unsupported claims or fix citation mismatches.
- Maintain original meaning and tone of the text.
- You MUST create the ## References section. This is mandatory.


OUTPUT EXAMPLE:
Artificial Intelligence is... [1]. Machine learning approaches... [2].

## References
[1] Smith, J. (2020). AI fundamentals. arXiv:2001.12345.
[2] Jones, M. (2021). Machine learning. arXiv:2102.54321.

"""
    
    expected_output = f"""
        
Fact-checked text with verified citations. 
MUST include ## References section in APA7 format.
Start with summary text, then blank line, then ## References.

"""
    
    context = [reviewer_task]

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context
    )