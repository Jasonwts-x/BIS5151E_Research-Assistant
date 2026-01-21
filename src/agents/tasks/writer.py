from __future__ import annotations

from crewai import Task


def create_writer_task(agent, topic: str, context: str) -> Task:
    """
    Create the writer task with explicit anti-hallucination instructions.

    Args:
        agent: The Writer agent
        topic: Research topic/question
        context: Retrieved context from RAG pipeline
    """
    description = f"""
Write a concise literature-style summary on the topic: "{topic}"

⚠️ CRITICAL RULES - VIOLATION WILL RESULT IN REJECTION:
1. Use ONLY information from the context below
2. NEVER invent citations, sources, or facts
3. If the context doesn't cover something, DON'T mention it
4. Every factual claim MUST have a citation [1], [2], etc.
5. If uncertain, use cautious language: "may", "suggests", "appears to"

AVAILABLE CONTEXT (Your ONLY source of information):
{context}

Guidelines:
- Write 300 words maximum
- Use neutral, academic tone
- Focus on what the context ACTUALLY says
- Include inline citations for every claim: [1], [2], etc.
- Structure: Introduction → Key concepts → Conclusion

REMEMBER: The context above is your ONLY source. Do not add anything not explicitly stated there.

Your task: Write a clear, accurate summary that synthesizes the key ideas from the PROVIDED context.
"""

    return Task(
        description=description,
        expected_output=(
            "A 300-word academic summary with inline citations [1], [2], etc. "
            "that accurately represents ONLY the information from the provided context. "
            "Every factual claim must be traceable to a source in the context."
        ),
        agent=agent,
    )