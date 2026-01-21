from __future__ import annotations

from crewai import Task


def create_reviewer_task(agent, writer_task: Task) -> Task:
    """
    Create the reviewer task.
    
    Args:
        agent: The Reviewer agent
        writer_task: The previous writer task (for context)
    """
    description = """
Review and improve the research summary from the previous writing task.

⚠️ CRITICAL CONSTRAINTS:
1. Improve ONLY clarity, grammar, and sentence structure
2. Do NOT add any new facts, claims, or information
3. Do NOT add or change any citations
4. Do NOT expand the content
5. Preserve the exact meaning of every statement

Your ONLY allowed changes:
✓ Fix grammar and spelling
✓ Improve sentence flow
✓ Enhance readability
✓ Adjust word choice for better clarity (without changing meaning)

Your FORBIDDEN changes:
✗ Adding new information
✗ Adding new citations
✗ Removing citations
✗ Changing the meaning of any claim
✗ Expanding on ideas

Your task: Return an improved version that is clearer and more polished while preserving all original claims and citations EXACTLY.
"""

    return Task(
        description=description,
        expected_output=(
            "An improved version of the draft with better clarity, coherence, and academic style. "
            "All original citations [1], [2], etc. must be preserved exactly. "
            "No new facts or citations should be added. "
            "The meaning of every statement must remain unchanged."
        ),
        agent=agent,
        context=[writer_task]
    )