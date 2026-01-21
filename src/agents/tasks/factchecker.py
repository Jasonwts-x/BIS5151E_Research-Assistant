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

CRITICAL INSTRUCTION:
You must return the COMPLETE, FULL TEXT of the fact-checked summary.
Do NOT return a description of what you did or a meta-explanation.
Return the actual text content that should be shown to the user.

Example of CORRECT output:
"AI, or Artificial Intelligence, refers to the simulation of human intelligence in machines [1]. 
It encompasses various subfields including machine learning and natural language processing [2]..."

Example of INCORRECT output:
"A fact-checked version of the text where all claims are verified..." ❌
"""

    return Task(
        description=description,
        expected_output=(
            "The COMPLETE fact-checked text (5-8 sentences) with:\n"
            "- Full paragraph text, not a description\n"
            "- All factual claims verified against the source context\n"
            "- All citations [1], [2], etc. accurate and properly formatted\n"
            "- Unsupported claims removed or softened with cautious language\n"
            "- No new citations or facts fabricated\n"
            "- Academic tone maintained\n\n"
            "OUTPUT MUST BE THE ACTUAL TEXT, NOT A SUMMARY OF WHAT WAS DONE."
        ),
        agent=agent,
        context=[reviewer_task]
    )
