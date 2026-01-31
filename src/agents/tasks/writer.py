from crewai import Task
 
def create_writer_task(agent, topic: str, context: str, mode: str = "strict") -> Task:
    if mode == "strict":
        description = f"""
        You are an academic writer.
   
        TOPIC: {topic}
   
        SOURCES (Pre-Summarized):
        {context}
   
        TASK:
        Write a coherent research summary (200-300 words) based on the SOURCES.
   
        CRITICAL RULES:
        1. Start with a clear introduction sentence.
        2. Use inline citations like [1], [2] immediately after facts.
        3. NO LATEX / MATH FORMATTING: Do NOT use symbols like \\( t \\), $x$, or \\( q_t \\).
            - Instead of "\\( t \\)", write "time t".
            - Instead of "\\( qry(\\cdot) \\)", write "the query function".
            - Write for a general reader, not a mathematician.
        """
   
        return Task(
            description=description,
            expected_output="A comprehensive text summary based on the provided sources.",
            agent=agent
        )

    else:
        return Task(
            description=f"Write a short summary (200-300 words) about '{topic}'. Use general knowledge.",
            expected_output="Short text summary.",
            agent=agent
        )