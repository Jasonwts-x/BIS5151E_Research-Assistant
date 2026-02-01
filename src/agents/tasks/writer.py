"""
Writer Task Definition.

Defines the writing task with instructions and expected output.
Supports both default mode (with context) and fallback mode (general knowledge).

Architecture:
    Task is passed to the Writer agent during crew execution.
"""
from __future__ import annotations

from crewai import Task


def create_writer_task(agent, topic: str, context: str, mode: str = "default") -> Task:
    """
    Create writer task with mode-specific instructions.
    
    Args:
        agent: Writer agent instance
        topic: Research topic
        context: Retrieved context (may be empty)
        mode: "default" (with context) or "fallback" (general knowledge)
        
    Returns:
        Configured Task instance
    """

    if mode == "default":
        
        description = f"""DEFAULT MODE:

TOPIC: 
{topic}
   
SOURCES:
{context}
   
TASK: Write a coherent RESEARCH SUMMARY (200-300 words) based on the SOURCES.
   
REQUIREMENTS:
1. Begin with a clear introduction sentence.
2. Cite all factual claims using inline citations like [1], [2] immediately after facts.
3. Write in plain English (no LaTeX or math formatting: use "time t" not "\\(t\\)")

"""

        expected_output = f"""
        
A well-structured summary of 200–300 words
that accurately reflects the information from the sources 
and includes proper in-text citations ([1], [2], etc.).
        
"""

    else:

        description = f"""FALLBACK MODE:

TOPIC: 
{topic}

NOTE: NO specific SOURCES available. Use general academic knowledge.

TASK: Write a 200-300 word EDUVATIONAL SUMMARY about '{topic}'.

REQUIREMENTS:
1. Use cautious language: "typically", "may", "often".
2. Do NOT include citation numbers [1], [2], etc.
3. Focus on foundational concepts.

"""

        expected_output = f"""
        
A clear and concise, 200-300 words, educational summary without citations.
        
"""
    
    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent
    )