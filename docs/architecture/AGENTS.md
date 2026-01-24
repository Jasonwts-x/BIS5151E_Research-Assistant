# Multi-Agent System Architecture

Detailed documentation of the CrewAI multi-agent workflow.

---

## Overview

The agent system uses **CrewAI** to orchestrate multiple AI agents that collaborate to produce high-quality, fact-checked summaries.

**Philosophy:** Divide complex tasks into specialized roles, each with clear responsibilities.

---

## Agent Architecture
```
Query + Context
      ↓
┌─────────────────────────────────────┐
│         Research Crew               │
│                                     │
│  ┌──────────┐   ┌──────────────┐  │
│  │  Writer  │ → │   Reviewer   │  │
│  │  Agent   │   │    Agent     │  │
│  └──────────┘   └──────┬───────┘  │
│                        │           │
│                        ↓           │
│                 ┌──────────────┐  │
│                 │ FactChecker  │  │
│                 │    Agent     │  │
│                 └──────────────┘  │
│                        ↓           │
└────────────────────────┼───────────┘
                         ↓
                  Final Summary
               (fact-checked & cited)
```

---

## Agent Roles

### 1. Writer Agent

**Role:** Research writer and summarizer

**Goal:** Draft accurate summaries from provided context

**Backstory:**
> "You are an experienced research writer specializing in academic literature reviews. Your strength is synthesizing complex information into clear, concise summaries with proper citations."

**Responsibilities:**
- Read and understand the context
- Extract key points
- Write coherent summary (300 words max)
- Add inline citations [1], [2], etc.
- Use neutral, academic tone

**Task:**
```yaml
description: >
  Write a concise research summary on the topic: {topic}.
  
  Requirements:
  - 300 words maximum
  - Academic tone
  - Use ONLY information from provided context
  - Include inline citations [1], [2], etc.
  - Do NOT fabricate information
  
  Context available:
  {context}

expected_output: >
  A well-written draft summary with inline citations.
```

**Example output:**
```
Machine learning is a subset of artificial intelligence that enables 
systems to learn from data without explicit programming [1]. The field 
has evolved significantly, with modern approaches using neural networks 
and deep learning architectures [2]. Key applications include natural 
language processing, computer vision, and predictive analytics [1][3].
```

---

### 2. Reviewer Agent

**Role:** Content reviewer and editor

**Goal:** Improve clarity, coherence, and readability

**Backstory:**
> "You are a meticulous editor with expertise in academic writing. Your role is to polish drafts while preserving factual accuracy and citations."

**Responsibilities:**
- Review the draft summary
- Improve sentence structure
- Enhance clarity and flow
- Fix grammar and style issues
- **Preserve all citations**
- Do NOT add new facts

**Task:**
```yaml
description: >
  Review and improve the following draft summary.
  
  Requirements:
  - Improve clarity and coherence
  - Fix grammar and sentence structure
  - Ensure logical flow
  - Keep the same meaning and claims
  - Do NOT add new facts
  - Do NOT remove citations
  
  Draft to review:
  {draft}

expected_output: >
  An improved version with better clarity and structure.
```

**Example transformation:**

**Before (Writer output):**
```
Machine learning is a subset of AI that enables systems to learn from 
data without explicit programming [1]. Modern approaches use neural 
networks [2]. Applications include NLP and computer vision [3].
```

**After (Reviewer output):**
```
Machine learning, a subset of artificial intelligence, enables systems 
to learn from data without requiring explicit programming [1]. Modern 
approaches leverage neural networks and deep learning architectures to 
achieve state-of-the-art results [2]. Key applications span natural 
language processing, computer vision, and predictive analytics [3].
```

---

### 3. FactChecker Agent

**Role:** Fact verifier and citation validator

**Goal:** Ensure all claims are supported by context

**Backstory:**
> "You are a rigorous fact-checker who verifies every claim against source documents. You flag unsupported claims and ensure proper attribution."

**Responsibilities:**
- Verify each claim against context
- Check citation consistency
- Flag unsupported statements
- Suggest hedging language if needed
- Ensure no hallucinations

**Task:**
```yaml
description: >
  Fact-check the following text and validate citations.
  
  Requirements:
  - Verify all claims are supported by context
  - Ensure citations [1], [2], etc. are consistent
  - Flag any unsupported or speculative claims
  - Suggest hedging language if needed ("may", "suggests", "appears to")
  - Do NOT invent new sources
  
  Context for verification:
  {context}
  
  Text to check:
  {reviewed_text}

expected_output: >
  A fact-checked version with verified claims and consistent citations.
```

**Example corrections:**

**Input:**
```
Machine learning revolutionized AI in 2010 [1]. All modern systems use 
deep learning [2]. It will replace human intelligence by 2030.
```

**FactChecker identifies:**
1. ❌ "revolutionized AI in 2010" - Not in context, overly specific
2. ❌ "All modern systems" - Overgeneralization
3. ❌ "will replace human intelligence by 2030" - Speculation, no citation

**Corrected output:**
```
Machine learning has significantly advanced AI capabilities [1]. Many 
modern systems leverage deep learning techniques [2]. The technology 
continues to evolve rapidly [1].
```

---

## Crew Configuration

**File:** `src/agents/crews/research_crew.py`
```python
from crewai import Crew, Agent, Task, LLM

class ResearchCrew:
    def __init__(self, llm: LLM):
        self.llm = llm
        
    def create_crew(self, topic: str, context: str, language: str):
        # Create agents
        writer = Agent(
            role="Research Writer",
            goal="Write accurate summaries from context",
            backstory="Experienced academic writer...",
            llm=self.llm,
            verbose=True
        )
        
        reviewer = Agent(
            role="Content Reviewer",
            goal="Improve clarity and coherence",
            backstory="Meticulous editor...",
            llm=self.llm,
            verbose=True
        )
        
        fact_checker = Agent(
            role="Fact Checker",
            goal="Verify all claims",
            backstory="Rigorous fact verifier...",
            llm=self.llm,
            verbose=True
        )
        
        # Create tasks
        write_task = Task(
            description=f"Write summary on: {topic}\nContext: {context}",
            expected_output="Draft with citations",
            agent=writer
        )
        
        review_task = Task(
            description="Review and improve draft",
            expected_output="Improved draft",
            agent=reviewer
        )
        
        check_task = Task(
            description="Fact-check and validate",
            expected_output="Final fact-checked summary",
            agent=fact_checker
        )
        
        # Create crew
        crew = Crew(
            agents=[writer, reviewer, fact_checker],
            tasks=[write_task, review_task, check_task],
            verbose=True
        )
        
        return crew
```

---

## Execution Flow

### Sequential Execution
```
1. Initialize Crew
   ├─ Load LLM (Ollama qwen2.5:3b)
   ├─ Create 3 agents
   └─ Define 3 tasks

2. Execute Task 1: Writing
   ├─ Writer receives: topic + context
   ├─ Writer calls LLM to generate draft
   ├─ Output: Draft summary with citations
   └─ Time: ~10 seconds

3. Execute Task 2: Review
   ├─ Reviewer receives: draft from Task 1
   ├─ Reviewer calls LLM to improve draft
   ├─ Output: Improved draft
   └─ Time: ~5 seconds

4. Execute Task 3: Fact-Checking
   ├─ FactChecker receives: improved draft + context
   ├─ FactChecker calls LLM to verify claims
   ├─ Output: Final fact-checked summary
   └─ Time: ~10 seconds

5. Return Result
   └─ Final output: Verified summary with citations
```

**Total execution time:** ~25-30 seconds

---

## LLM Configuration

### Ollama Integration
```python
from crewai import LLM

llm = LLM(
    model="ollama/qwen2.5:3b",
    base_url="http://ollama:11434",
    temperature=0.3  # Low temperature for factual outputs
)
```

**Why qwen2.5:3b?**
- ✅ Fast inference (~2s per call)
- ✅ Good instruction following
- ✅ Multilingual support
- ✅ Runs on CPU
- ✅ Open-source

**Temperature setting:**
- `0.3` = More deterministic, factual
- Higher values = More creative, variable

---

## Guardrails & Safety

### Content Safety

**Location:** `src/eval/guardrails.py`
```python
class GuardrailsWrapper:
    def check_input(self, query: str) -> bool:
        """Check if query contains harmful content."""
        # Check for hate speech, violence, etc.
        pass
        
    def check_output(self, text: str) -> bool:
        """Check if output contains harmful content."""
        # Verify no offensive content in response
        pass
```

**Checks:**
- ❌ Hate speech
- ❌ Violence
- ❌ Misinformation patterns
- ❌ Personal information

### Hallucination Prevention

**Strategies:**
1. **Explicit instructions** - "Use ONLY provided context"
2. **Multi-agent review** - FactChecker validates Writer
3. **Low temperature** - Reduce randomness
4. **Citation requirement** - Every claim must have source
5. **Context grounding** - Compare output against context

---

## Monitoring

### TruLens Integration (Experimental)

**Location:** `src/eval/trulens.py`

**Metrics tracked:**
```python
{
    "answer_relevance": 0.85,      # How relevant is answer to query
    "context_relevance": 0.90,     # How relevant is retrieved context
    "groundedness": 0.92,          # Are claims grounded in context
    "citation_coverage": 0.88      # % of claims with citations
}
```

**Usage:**
```python
from src.eval.trulens import TruLensMonitor

monitor = TruLensMonitor(enabled=True)
monitor.log_interaction(
    topic=query,
    context=context,
    output=final_output,
    language=language
)

# View metrics
metrics = monitor.get_summary()
```

---

## Performance Optimization

### Current Performance

**Per-query metrics:**
- Writer: ~10s
- Reviewer: ~5s
- FactChecker: ~10s
- **Total: ~25s**

### Optimization Opportunities

1. **Parallel execution** (future)
```
   Instead of: Writer → Reviewer → FactChecker
   Do: Writer → (Reviewer || FactChecker) → Aggregator
   Savings: ~5s
```

2. **Streaming responses** (future)
```python
   for token in llm.stream(prompt):
       yield token
   # Shows progress to user
```

3. **Caching** (future)
```python
   @cache(ttl=3600)
   def generate_response(prompt_hash):
       # Cache identical prompts
       pass
```

4. **Model optimization**
   - Use quantized models (4-bit)
   - GPU acceleration
   - Smaller models for simple tasks

---

## Error Handling

### Agent Failures
```python
try:
    result = crew.kickoff(inputs={...})
except AgentExecutionError as e:
    logger.error(f"Agent failed: {e}")
    # Fallback: Return draft without fact-checking
    return {"answer": draft, "verified": False}
```

### LLM Failures
```python
@retry(tries=3, delay=2)
def call_llm(prompt):
    try:
        return llm.generate(prompt)
    except ConnectionError:
        logger.warning("LLM connection failed, retrying...")
        raise
```

---

## Future Agent Additions

### Planned Agents

1. **Translator Agent**
   - Translate summaries to target language
   - Preserve citations
   - Maintain academic tone

2. **Citation Formatter Agent**
   - Generate BibTeX, APA, MLA
   - Link citations to source documents
   - Create bibliography

3. **Quality Scorer Agent**
   - Evaluate summary quality
   - Provide improvement suggestions
   - Flag low-confidence outputs

4. **Research Planner Agent**
   - Break complex queries into sub-questions
   - Plan multi-step research
   - Aggregate results

---

## Debugging

### Enable Verbose Mode
```python
crew = Crew(
    agents=[...],
    tasks=[...],
    verbose=True  # Shows agent reasoning
)
```

**Output:**
```
[Writer] Thinking: I need to summarize the topic based on the context...
[Writer] Action: Drafting summary with key points from chunks 1, 3, 5...
[Writer] Output: Machine learning is a subset of AI that...

[Reviewer] Thinking: The draft is good but sentence 2 needs improvement...
[Reviewer] Action: Rephrasing for better clarity...
[Reviewer] Output: Machine learning, a subset of artificial intelligence...

[FactChecker] Thinking: Checking claim "subset of AI" against context...
[FactChecker] Action: Found supporting evidence in chunk 1...
[FactChecker] Output: Verified ✓
```

### View Agent Logs
```bash
# View CrewAI service logs
docker compose logs crewai -f
```

---

**[⬅ Back to Architecture](README.md)** | **[⬆ Back to Main README](../../README.md)**