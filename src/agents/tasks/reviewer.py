from crewai import Task
 
def create_reviewer_task(agent, writer_task) -> Task:
    return Task(
        description="""
        You are an Academic Editor. Review the draft text provided.
       
        GOALS:
        1. Improve flow and readability.
        2. Ensure citations [1] are preserved.
        3. ⛔ REMOVE LATEX: If you see symbols like \\( x \\) or $t$, replace them with plain English wording.
           - Bad: "The function \\( f(x) \\) is used."
           - Good: "The function f(x) is used."
       
        DO NOT change the Reference list at the end.
        """,
        expected_output="Polished text, free of LaTeX formatting.",
        agent=agent,
        context=[writer_task]
    )