from __future__ import annotations

from crewai import Task


def create_factchecker_task(agent, reviewer_task: Task, context: str) -> Task:
    """
    Create the fact-checker task with strict verification against context.

    Args:
        agent: The FactChecker agent
        reviewer_task: The previous reviewer task (for context)
        context: Retrieved context from RAG pipeline (GROUND TRUTH)
    """
    
    # Validate that context is actually provided
    if not context or "NO CONTEXT AVAILABLE" in context:
        # If no context, create a simplified task that just returns the reviewed text
        description = """
    NOTICE: No context documents were available for fact-checking.

    Since this summary was generated in fallback mode (using general knowledge),
    you should:
    1. Return the reviewed text AS-IS without modifications
    2. Do NOT add fake citations
    3. Do NOT remove the disclaimer note if present

    Simply return the complete reviewed text.
    """
        return Task(
            description=description,
            expected_output="The reviewed text returned unchanged (fallback mode).",
            agent=agent,
            context=[reviewer_task]
        )
    
    # Original strict mode task with proper context
    description = f"""
    CRITICAL TASK: Fact-check the reviewed text against the GROUND TRUTH context below.

    GROUND TRUTH SOURCES (Your ONLY reference for verification):
    {context}

    ⚠️ YOUR STRICT RESPONSIBILITIES:
    1. **Cross-reference EVERY claim** against the sources above
    2. **Verify EVERY citation** [1], [2], etc. matches the source numbering
    3. **Remove or flag** any claims not found in the sources
    4. **Remove or flag** any invented citations
    5. **Soften language** for claims that are implied but not explicit (use "may", "suggests", "appears to")
    6. **Preserve ONLY verified content**

    VERIFICATION CHECKLIST:
    □ Is this claim explicitly stated in the context? (If NO → Remove or soften)
    □ Does the citation [N] point to the correct source? (If NO → Fix or remove)
    □ Are there any statements without citations? (If YES → Add citation or remove)
    □ Are there any sources that aren't in the context? (If YES → Remove immediately)

    CRITICAL INSTRUCTION:
    You must return the COMPLETE, FULL TEXT of the fact-checked summary.
    Do NOT return a description of what you did or a meta-explanation.
    Return the actual text content that should be shown to the user.

    If you find multiple unsupported claims, you may need to significantly shorten the text.
    That's okay - accuracy is more important than length.

    Example of CORRECT output:
    "Generative AI refers to systems that can create new content based on patterns in training data [1]. 
    These systems include large language models that process natural language [2]."

    Example of INCORRECT output:
    "I verified the claims and found that..." ❌
    "A fact-checked version where..." ❌
    """

    return Task(
        description=description,
        expected_output=(
            "The COMPLETE fact-checked text where:\\n"
            "- EVERY claim is verified against the provided context\\n"
            "- EVERY citation [1], [2], etc. is accurate and matches the sources\\n"
            "- ALL unsupported claims have been removed or softened\\n"
            "- NO invented sources or citations remain\\n"
            "- Text may be shorter than input if claims couldn't be verified\\n\\n"
            "OUTPUT MUST BE THE ACTUAL TEXT, NOT A DESCRIPTION."
        ),
        agent=agent,
        context=[reviewer_task]
    )