from crewai import Task
 
def create_factchecker_task(agent, reviewer_task, context: str) -> Task:
    """Create fact-checking task with strict output rules."""

    return Task(
        description=f"""
        Fact-check the reviewed text against sources. Remove unsupported claims.
       
        YOUR TASK:
        1. Output the Draft Text EXACTLY as is.
        2. Verify every claim has citation [1], [2], etc.
        3. Every citation must match SOURCE [N] in context below
        4. Remove any unsupported claims
        5. Create a "## References" section at the end.
        6. Match every citation [1] in the text to 'SOURCE [1]' in the context.
        7. Use the "METADATA" line from the context to format the reference in APA7 style.

        OUTPUT FORMAT:
        - Start directly with summary text
        - NO meta-commentary like "Here is the text..."
        - Include inline citations [1], [2] after each claim
        - End with "## References" section
        - List each source as: [N] Author. (Year). Title.
        - Use title case (not ALL CAPS) for titles
        - If metadata incomplete, use filename as title

        APA7 FORMAT:
        [1] Author, A. B. (Year). Paper title. Journal/Source.

        For arXiv: [1] Author, A. (Year). Title. arXiv:XXXX.XXXXX.
        For unknown: [1] Unknown. (n.d.). [Filename].

        SOURCES:
        {context}
        """,
        expected_output="Summary with inline citations + References section (no preamble)",
        agent=agent,
        context=[reviewer_task]
    )
 