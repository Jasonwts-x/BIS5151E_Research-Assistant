from __future__ import annotations
 
from typing import List, Optional
from pydantic import BaseModel, Field
 
from crewai import Task
 
 
class SummaryOutput(BaseModel):
    """Structured output for the Writer task with mandatory citations."""
    content: str = Field(
        ...,
        description="The main summary text with inline citations like [1], [2], [3]"
    )
    references: List[str] = Field(
        ...,
        description="List of source references, each starting with [1], [2], etc."
    )
 
 
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
        # ===================================================================
        # FALLBACK MODE: No context available, general knowledge only
        # ===================================================================
        description = f"""Write a concise educational summary on the topic: "{topic}"
 
⚠️ FALLBACK MODE: No specific research documents were found.
 
INSTRUCTIONS:
1. Use established academic knowledge
2. Use cautious language: "generally", "typically", "may", "tends to"
3. 250-300 words
4. DO NOT invent citations or references
5. Be clear about limitations
 
OUTPUT FORMAT:
Write your summary as plain text (250-300 words).
Do NOT include citations like [1], [2].
End with a note explaining no specific sources were found.
"""
       
        expected_output = (
            "An educational summary of 250-300 words based on general knowledge. "
            "NO citations. Clear, factual, with cautious language."
        )
       
        # Don't use Pydantic for fallback - simpler text output
        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent
        )
 
    else:  # STRICT MODE
        # ===================================================================
        # STRICT MODE: Context available, citations MANDATORY
        # ===================================================================
       
        # Extract sources from context for explicit listing
        sources = _extract_sources_from_context(context)
        source_list = "\n".join(f"[{i+1}] {src}" for i, src in enumerate(sources))
       
        description = f"""Write a research summary on: "{topic}"
 
═══════════════════════════════════════════════════════════════
⚠️ CRITICAL: YOU MUST INCLUDE CITATIONS IN EVERY SENTENCE ⚠️
═══════════════════════════════════════════════════════════════
 
MANDATORY RULES (FAILURE = REJECTION):
 
1. CITATIONS ARE REQUIRED
   - Every factual sentence MUST end with [1] or [2] etc.
   - Example: "Machine learning uses data to improve performance [1]."
   - Multiple sources: "Deep learning has many applications [1][2]."
   - You MUST include at least 10 citations in your summary
 
2. USE ONLY THESE SOURCES
{source_list}
 
3. NEVER invent sources not listed above
4. NEVER write a sentence without a citation
 
AVAILABLE CONTEXT:
{context}
 
OUTPUT REQUIREMENTS:
 
Write your summary in this EXACT format:
 
[Write 4-6 sentences about the topic. EVERY sentence must have [1], [2] etc.]
 
## References
[1] First source name
[2] Second source name
[3] Third source name
 
EXAMPLE OUTPUT:
Machine learning is a subset of artificial intelligence [1]. It enables computers to learn from data [1][2]. Neural networks are commonly used in deep learning [2]. These systems can recognize patterns in images and text [2][3].
 
## References
[1] arxiv-2104.05314-machine-learning.pdf
[2] arxiv-1601.03642-deep-learning.pdf
[3] arxiv-2201.12345-neural-networks.pdf
 
═══════════════════════════════════════════════════════════════
⚠️ REMEMBER: If you submit text without [1], [2] etc., it will be REJECTED
═══════════════════════════════════════════════════════════════
"""
       
        expected_output = (
            "A summary with inline citations [1], [2] in EVERY sentence. "
            "Followed by a ## References section listing all sources. "
            "Minimum 10 citations total."
        )
       
        # Try WITHOUT Pydantic first - direct text output
        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent
            # NO output_pydantic - let agent return plain text
        )
 
 
def _extract_sources_from_context(context: str) -> List[str]:
    """
    Extract source names from formatted context.
   
    Args:
        context: Formatted context string with SOURCE markers
       
    Returns:
        List of source names (e.g., ["arxiv-123.pdf", "paper.pdf"])
    """
    import re
   
    # Find all lines matching: [1] source-name.pdf or SOURCE [1]: source-name
    sources = []
   
    # Pattern 1: "[1] filename.pdf" at start of line
    pattern1 = re.findall(r'^\s*\[(\d+)\]\s+(.+?)(?:\n|$)', context, re.MULTILINE)
    for num, source in pattern1:
        sources.append(source.strip())
   
    # Pattern 2: "SOURCE [1]: filename.pdf"
    pattern2 = re.findall(r'SOURCE\s*\[(\d+)\]:\s*(.+?)(?:\n|$)', context, re.MULTILINE)
    for num, source in pattern2:
        if source.strip() not in sources:
            sources.append(source.strip())
   
    # Remove duplicates while preserving order
    seen = set()
    unique_sources = []
    for src in sources:
        if src not in seen:
            seen.add(src)
            unique_sources.append(src)
   
    return unique_sources if unique_sources else ["Context provided"]
 