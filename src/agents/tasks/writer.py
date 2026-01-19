from __future__ import annotations

from crewai import Task


def create_writer_task(agent, topic: str, context: str) -> Task:
    """
    Create the writer task.

    Args:
        agent: The Writer agent
        topic: Research topic/question
        context: Retrieved context from RAG pipeline
    """
    description = f"""
Write a concise literature-style summary on the topic: "{topic}"

Guidelines:
- Write 5-8 sentences
- Use a neutral, academic tone
- Focus on key concepts and relationships
- Use the provided context to support your points
- Include inline citations using [1], [2], etc. format

Context from retrieved documents:
{context}

Your task: Write a clear, well-structured summary that synthesizes the key ideas.
"""

    return Task(
        description=description,
        expected_output=(
            "A 5-8 sentence academic summary with inline citations [1], [2], etc. "
            "that accurately represents the key concepts from the provided context."
        ),
        agent=agent,
    )
