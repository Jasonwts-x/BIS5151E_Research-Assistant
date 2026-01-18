from __future__ import annotations

from crewai import Task


def create_reviewer_task(agent, draft: str) -> Task:
    """
    Create the reviewer task.
    
    Args:
        agent: The Reviewer agent
        draft: The draft text to review
    """
    description = f"""
Review and improve the following draft summary:

{draft}

Your responsibilities:
- Improve clarity, coherence, and flow
- Enhance academic writing style
- Ensure logical structure
- Maintain all factual claims and citations EXACTLY as written
- Do NOT add new information or citations
- Do NOT change the meaning of any statements

Your task: Return an improved version that is clearer and more polished while preserving all original claims and citations.
"""

    return Task(
        description=description,
        expected_output=(
            "An improved version of the draft with better clarity, coherence, and academic style. "
            "All original citations [1], [2], etc. must be preserved exactly. "
            "No new facts or citations should be added."
        ),
        agent=agent,
    )