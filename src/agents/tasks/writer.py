from __future__ import annotations

from crewai import Task


def create_writer_task(agent, topic: str, context: str, mode: str = "strict") -> Task:
    """
    Create the writer task with appropriate instructions based on mode.
    
    Args:
        agent: The Writer agent
        topic: Research topic
        context: Retrieved context (may be empty in fallback mode)
        mode: "strict" (with context) or "fallback" (without context)
    """

    if mode == "fallback":
        description = f"""Write a concise educational summary on the topic: "{topic}"

    ⚠️ NOTICE: No specific research documents were found in the database for this topic.

    FALLBACK MODE INSTRUCTIONS:
    1. Provide a general overview based on established academic knowledge
    2. Use cautious, academic language: "generally", "typically", "commonly"
    3. Focus on well-established concepts and definitions
    4. DO NOT invent specific citations or paper references
    5. Be educational and informative while being honest about limitations
    6. Use your training knowledge to provide accurate, helpful information

    Guidelines:
    - Write 250-300 words
    - Use neutral, academic tone
    - Structure: Introduction → Key concepts → Current understanding
    - NO fake citations like [1], [2], etc.
    - DO NOT mention specific papers, authors, or years unless they are foundational/historical
    - Focus on explaining concepts clearly and accurately

    MANDATORY OUTPUT FORMAT:

    [Your educational summary without fake citations]

    ## Note
    This summary is based on general academic knowledge. No specific research papers were retrieved from the database for this query. To find relevant research papers, try:
    - Using more specific search terms related to your topic
    - Searching ArXiv.org directly with targeted keywords
    - Consulting specialized academic databases in your field of interest

    Remember: Provide genuinely helpful educational content based on established knowledge.
    """
        
        expected_output = (
            "An educational summary of 250-300 words based on general academic knowledge. "
            "NO citations or references to specific papers. "
            "Must include an informative note about the lack of specific sources. "
            "Content should be factually accurate and helpful."
        )
    

    else:  # strict mode
        description = f"""Write a concise literature-style summary on the topic: "{topic}"

    ⚠️ CRITICAL RULES - VIOLATION WILL RESULT IN REJECTION:
    1. Use ONLY information from the context below
    2. NEVER invent citations, sources, or facts
    3. If the context doesn't cover something, DON'T mention it
    4. Every factual claim MUST have a citation [1], [2], etc.
    5. If uncertain, use cautious language: "may", "suggests", "appears to"
    6. You MUST list all sources at the end under "## References"

    AVAILABLE CONTEXT (Your ONLY source of information):
    {context}

    Guidelines:
    - Write 300 words maximum
    - Use neutral, academic tone
    - Focus on what the context ACTUALLY says
    - Include inline citations for every claim: [1], [2], etc.
    - Structure: Introduction → Key concepts → Conclusion
    - END with a "## References" section listing ALL sources from the context

    MANDATORY OUTPUT FORMAT:

    [Your summary text with citations [1], [2], etc.]

    ## References
    [1] First source from context
    [2] Second source from context
    [3] Third source from context
    ...

    ⚠️ IMPORTANT:
    - Every source in the context must appear in References
    - Every claim must be cited
    - Do NOT add information not in the context

    REMEMBER: The context above is your ONLY source. Do not add anything not explicitly stated there.
    """
        
        expected_output = (
            "A well-structured academic summary with inline citations [1], [2], etc. "
            "Must include a '## References' section listing ALL sources from the context. "
            "Every claim must be supported by the provided context."
        )
    
    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
    )