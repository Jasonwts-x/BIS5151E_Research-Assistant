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
    Review the writer's output for clarity, coherence, and quality.

    Your responsibilities:
    1. **Improve clarity**: Simplify complex sentences, fix ambiguous phrasing
    2. **Check structure**: Ensure logical flow from introduction to conclusion
    3. **Verify completeness**: Check if all key aspects of the topic are covered
    4. **Enhance readability**: Improve transitions between ideas
    5. **Maintain academic tone**: Ensure professional, neutral language
    6. **Check formatting**: Verify proper citation format and reference section (if applicable)

    ⚠️ CRITICAL CONSTRAINTS:
    1. Improve ONLY clarity, grammar, spelling and sentence structure
    2. Do NOT add any new facts, claims, or information
    3. Do NOT add, change or remove any citations
    4. Do NOT change the meaning of statements
    5. Do NOT expand the content
    6. Preserve the exact meaning of every statement
    7. Focus on presentation and clarity, not content accuracy (fact-checker handles that)

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

    Return the complete, improved text ready for fact-checking.
    """

    return Task(
        description=description,
        expected_output=(
            "A polished, well-structured version of the writer's text. "
            "Improved clarity and readability while preserving all factual claims and citations. "
            "Ready for fact-checking."
        ),
        agent=agent,
        context=[writer_task]
    )