from crewai import Task
 
def create_factchecker_task(agent, reviewer_task, context: str) -> Task:
    """
    Fact Checker task - APA7 Formatting.
    """
    return Task(
        description=f"""
        You are the final gatekeeper.
       
        INPUT:
        1. Draft Text
        2. Source Context (containing "METADATA: Author (Year). Title")
       
        YOUR TASK:
        1. Output the Draft Text EXACTLY as is.
        2. Create a "## References" section at the end.
        3. Match every citation [1] in the text to 'SOURCE [1]' in the context.
        4. Use the "METADATA" line from the context to format the reference in APA7 style.
       
        EXAMPLE:
        Context: "SOURCE [1] ... METADATA: Smith (2023). AI Advances"
        Output Reference: "[1] Smith. (2023). AI Advances."
 
        ⚠️ STRICT RULES:
        - DO NOT start with "Here is the answer" or "This is the criteria".
        - START DIRECTLY with the text content.
        - If metadata is missing, use the filename.
 
        SOURCE CONTEXT:
        {context}
        """,
        expected_output="The full text followed by APA7 references.",
        agent=agent,
        context=[reviewer_task]
    )
 