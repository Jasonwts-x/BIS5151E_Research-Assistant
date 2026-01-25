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
    
    # Check if we're in fallback mode (no context available)
    if not context or "NO CONTEXT AVAILABLE" in context:
        description = """
    ⚠️ FALLBACK MODE FACT-CHECKING
    
    Since no specific research documents are available, your role is to:
    
    1. **Verify Claim Reasonableness**:
       - Check that all claims are well-established academic knowledge
       - Flag any claims that seem speculative or controversial
       - Ensure proper use of hedging language ("may", "typically", "generally")
    
    2. **Check for Inappropriate Definitiveness**:
       - Remove any overly confident statements about cutting-edge research
       - Flag claims about specific papers, authors, or years (none should exist)
       - Ensure no fake citations like [1], [2], etc. are present
    
    3. **Verify Academic Standards**:
       - Check that the summary maintains neutral, academic tone
       - Ensure concepts are explained clearly and accurately
       - Verify that uncertainty is acknowledged appropriately
    
    4. **Ensure Proper Disclaimer**:
       - Confirm the "Note" section is present and accurate
       - The note should clearly state this is based on general knowledge
       - It should suggest ways to find specific research papers
    
    5. **Quality Standards**:
       - Content should be educational and informative
       - No invented information or misleading statements
       - Proper structure (Introduction → Key concepts → Current understanding)
    
    ⚠️ CRITICAL: If you find ANY specific citations [1], [2], invented paper 
    references, or claims that seem too specific to be general knowledge, 
    you MUST remove or soften them.
    
    Return the complete, verified text ready for the user.
    """
        
        return Task(
            description=description,
            expected_output=(
                "The reviewed text with quality checks applied. "
                "All claims verified to be reasonable general knowledge. "
                "No fake citations or overly specific claims. "
                "Proper disclaimer included. "
                "Maintains educational value while being honest about limitations."
            ),
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
    "I verified the claims and found that..."
    "I've reviewed the text and found 3 claims that need revision..." 
    "A fact-checked version where..."
    (This is a meta-description, NOT the actual output we need!)

    Remember: Return the FULL TEXT of the fact-checked summary, not a description of your work.
    """

    return Task(
        description=description,
        expected_output=(
            "The complete fact-checked summary text with all claims verified against sources. "
            "All citations accurate and properly formatted. "
            "Any unsupported claims removed or softened. "
            "Ready to be presented to the user."
        ),
        agent=agent,
        context=[reviewer_task]
    )