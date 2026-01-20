from __future__ import annotations

from crewai import Task


def create_factchecker_task(agent, reviewer_task: Task, context: str) -> Task:
    """
    Create the fact-checker task.

    Args:
        agent: The FactChecker agent
        reviewer_task: The previous reviewer task (for context)
        context: Retrieved context from RAG pipeline
    """
    description = f"""
Fact-check the reviewed text from the previous task against the provided context.

Source context:
{context}

Your responsibilities:
1. Verify that all factual claims are supported by the provided context
2. Ensure all citations [1], [2], etc. match the sources in the context
3. Flag any unsupported or speculative statements
4. For uncertain claims, suggest more cautious wording (e.g., "may", "suggests", "appears to")
5. Do NOT fabricate new citations
6. Do NOT add information not present in the original text

Your task: Return a fact-checked version where all claims are properly supported and citations are accurate.
If you find unsupported claims, either remove them or soften the language appropriately.
"""

    return Task(
        description=description,
        expected_output=(
            "A fact-checked version of the text where:\n"
            "- All factual claims are verified against the source context\n"
            "- All citations are accurate and properly formatted\n"
            "- Unsupported claims are either removed or softened with cautious language\n"
            "- No new citations or facts are fabricated"
        ),
        agent=agent,
        context=[reviewer_task]  # ✅ Access output from reviewer_task automatically
    )
