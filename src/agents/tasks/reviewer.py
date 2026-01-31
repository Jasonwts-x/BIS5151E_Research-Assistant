"""Reviewer Task Definition"""
from crewai import Task


def create_reviewer_task(agent, writer_task) -> Task:
    """Create reviewer task with minimal necessary instructions."""

    description = f"""

TASK: Review and improve the draft text.

IMPROVE:
- Sentence structure and grammar
- Flow and clarity
- Academic tone

PRESERVE:
- All citations [1], [2], etc.
- All factual claims
- Original meaning

REMOVE: Any LaTeX notation (\\(x\\), $t$, etc.)

"""
    
    expected_output = "Improved draft. Same content and citations. No LaTeX."
    
    context = [writer_task]

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context
    )