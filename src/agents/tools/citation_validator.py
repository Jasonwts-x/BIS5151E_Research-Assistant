"""
Citation Validation Tool.

Validates that citations in text match sources in context.
Helps FactChecker agent verify citation accuracy programmatically.

Architecture:
    CrewAI tool decorator enables use by agents.
    Provides structured validation feedback to guide citation corrections.
"""
from __future__ import annotations

import re
from typing import Dict

from crewai.tools import tool


@tool
def validate_citation(text: str, citation_num: int, context: str) -> Dict[str, any]:
    """
    Validate that a citation [N] is properly used in text and exists in context.
    
    Args:
        text: Text containing citation
        citation_num: Citation number to validate
        context: Source context with SOURCE markers
        
    Returns:
        Dictionary with validation result and suggestions
    """
    # Check if citation exists in text
    citation_pattern = rf'\[{citation_num}\]'
    citation_matches = re.findall(citation_pattern, text)
    
    if not citation_matches:
        return {
            "valid": False,
            "reason": f"Citation [{citation_num}] not found in text",
            "suggestions": [
                f"Add [{citation_num}] after relevant claims",
                "Check if citation number is correct",
            ]
        }
    
    # Check if citation is used multiple times (good practice)
    citation_count = len(citation_matches)
    
    # Check if source exists in context
    source_pattern = rf'SOURCE \[{citation_num}\]'
    source_match = re.search(source_pattern, context)
    
    if not source_match:
        return {
            "valid": False,
            "reason": f"Source [{citation_num}] not found in context",
            "suggestions": [
                f"Remove citation [{citation_num}] as source doesn't exist",
                "Check if source numbering is correct",
            ]
        }
    
    # Extract source details for verification
    source_section = context[source_match.start():source_match.start()+500]
    has_metadata = "METADATA:" in source_section
    
    # All checks passed
    return {
        "valid": True,
        "reason": f"Citation [{citation_num}] is valid and properly formatted",
        "citation_count": citation_count,
        "has_metadata": has_metadata,
        "suggestions": [] if citation_count > 1 else [
            f"Consider citing [{citation_num}] in multiple places if relevant"
        ]
    }