from __future__ import annotations
 
from crewai import Task
 
 
def create_factchecker_task(agent, reviewer_task: Task, context: str) -> Task:
    """
    Create the fact-checker task with strict verification against context.
 
    Args:
        agent: The FactChecker agent
        reviewer_task: The previous reviewer task (for context)
        context: Retrieved context from RAG pipeline (GROUND TRUTH)
    """
   
    # Check if we're in fallback mode (no context available)
    if not context or "⚠️ NO CONTEXT AVAILABLE ⚠️" in context:
        description = """
⚠️ FALLBACK MODE FACT-CHECKING
 
Since no specific research documents are available, your role is to:
 
1. **Verify Claim Reasonableness**:
   - Check that all claims are well-established academic knowledge
   - Flag any claims that seem speculative or controversial
   - Ensure proper use of hedging language ("may", "typically", "generally")
 
2. **Check for Inappropriate Citations**:
   - Remove any citations like [1], [2] etc. (none should exist)
   - Flag claims about specific papers, authors, or years
   - Ensure no invented references
 
3. **Verify Academic Standards**:
   - Check that the summary maintains neutral, academic tone
   - Ensure concepts are explained clearly and accurately
   - Verify that uncertainty is acknowledged appropriately
 
4. **Ensure Proper Disclaimer**:
   - Confirm a note about missing sources is present
   - Should suggest ways to find specific research papers
 
5. **Quality Standards**:
   - Content should be educational and informative
   - No invented information or misleading statements
   - Proper structure and flow
 
⚠️ CRITICAL OUTPUT FORMAT:
Return ONLY the fact-checked text. Do NOT add meta-commentary like:
- "I verified the claims..."
- "I found 3 issues..."
- "The fact-checked version is..."
 
Just return the clean, verified text ready for the user.
 
Example CORRECT output:
"Machine learning is a field of computer science that generally focuses on data-driven learning.
It typically involves training algorithms on datasets...
 
Note: No specific research sources were available for this summary."
 
Example INCORRECT output:
"I verified the summary and found it accurate. The fact-checked version is: [text]"
"""
       
        return Task(
            description=description,
            expected_output=(
                "The complete fact-checked text (250-300 words) with quality verification. "
                "NO citations (none should exist in fallback mode). "
                "Clear disclaimer about missing sources. "
                "Educational and accurate content. "
                "NO meta-commentary - just the final text."
            ),
            agent=agent,
            context=[reviewer_task]
        )
   
    # STRICT MODE: Verify against provided context
    description = f"""
CRITICAL TASK: Fact-check the reviewed text against the GROUND TRUTH context below.
 
GROUND TRUTH SOURCES (Your ONLY reference for verification):
{context}
 
⚠️ YOUR STRICT RESPONSIBILITIES:
 
1. **Cross-reference EVERY claim** against the sources above
2. **Verify EVERY citation** [1], [2], [3] etc. matches the source numbering
3. **Check the ## References section** - ensure all sources listed are from the context
4. **Remove or flag** any claims not found in the sources
5. **Remove or flag** any invented citations or sources
6. **Soften language** for claims that are implied but not explicit:
   - Use "may", "suggests", "appears to", "indicates"
   - Change "X is Y" → "X appears to be Y" if not explicitly stated
 
CITATION FORMAT VERIFICATION:
- Inline citations must use format: [1], [2], [3]
- Each citation must reference a source listed in the context
- References section must use format:
 
## References
[1] Author, A. (Year). Title. Source.
[2] Author, B. (Year). Title. Source.
 
VERIFICATION CHECKLIST (Check EACH point):
□ Is every factual claim explicitly stated in the context?
□ Does every citation [N] point to the correct source from the context?
□ Are all statements properly cited?
□ Does the ## References section match the context sources?
□ Are there any invented sources NOT in the context?
□ Is the citation format [1] [2] [3] used consistently?
 
⚠️ CRITICAL OUTPUT INSTRUCTION:
You MUST return the COMPLETE, FULL TEXT of the fact-checked summary.
 
DO NOT return:
- ❌ "I verified the claims and found..."
- ❌ "The fact-checked version is: ..."
- ❌ "After reviewing, I found 3 issues..."
- ❌ Any meta-commentary about what you did
 
DO return:
- ✅ The actual summary text with citations
- ✅ The ## References section
- ✅ Nothing else
 
CORRECT OUTPUT FORMAT:
 
Machine learning is a subset of artificial intelligence [1]. It enables systems to learn from data [1][2].
Deep learning uses neural networks [2][3]. These systems can recognize patterns [3].
 
## References
[1] Author, A. (Year). Title of Paper. arXiv preprint arXiv:1234.5678.
[2] Author, B. (Year). Another Paper Title. Source.
[3] Author, C. (Year). Third Paper. Source.
 
INCORRECT OUTPUT:
"I've fact-checked the summary and verified all claims against the sources. The corrected version is: [text]"
 
Remember: Return the ACTUAL TEXT, not a description of your work.
If you find unsupported claims, remove them and continue with verified content only.
"""
 
    return Task(
        description=description,
        expected_output=(
            "The complete fact-checked summary (up to 300 words) with inline citations [1], [2], [3]. "
            "Followed by ## References section with properly formatted sources. "
            "All claims verified against provided context. "
            "NO meta-commentary - ONLY the final text ready for the user."
        ),
        agent=agent,
        context=[reviewer_task]
    )
 