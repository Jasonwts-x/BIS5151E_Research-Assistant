# Evaluation Metrics Explained

Detailed explanation of all quality metrics used in ResearchAssistantGPT.

---

## 📊 Metric Categories

1. **RAG Quality Metrics** - TruLens-based
2. **Citation Metrics** - Guardrails-based
3. **Text Quality Metrics** - ROUGE, BLEU, Similarity
4. **Performance Metrics** - Timing and resources

---

## 🎯 RAG Quality Metrics (TruLens)

### Answer Relevance

**What it measures**: How well the answer addresses the original query.

**Score range**: 0.0 (irrelevant) to 1.0 (perfectly relevant)

**Target**: > 0.8

**How it's calculated**:
```python
# TruLens uses an LLM to evaluate:
# "Does this answer address the question?"
# Considers:
# - Query keywords present in answer
# - Semantic similarity to query
# - Directness of response
```

**Example**:
```
Query: "What are neural networks?"

Good Answer (score: 0.95):
"Neural networks are computational models inspired by 
biological neurons that learn patterns from data [1]."

Bad Answer (score: 0.3):
"Machine learning has many applications including 
computer vision and natural language processing [1]."
```

**When to investigate**:
- Score < 0.7: Answer may be off-topic
- Check if retrieved context is relevant
- Adjust `RAG_TOP_K` or `RAG_ALPHA`

---

### Context Relevance

**What it measures**: How relevant the retrieved documents are to the query.

**Score range**: 0.0 (irrelevant) to 1.0 (perfectly relevant)

**Target**: > 0.7

**How it's calculated**:
```python
# Evaluates each retrieved chunk:
# "Is this chunk relevant to answering the question?"
# Average across all retrieved chunks
```

**Example**:
```
Query: "What is deep learning?"

Good Context (score: 0.9):
"Deep learning is a subset of machine learning that 
uses neural networks with multiple layers..."

Bad Context (score: 0.2):
"The weather in California is generally mild..."
```

**When to investigate**:
- Score < 0.6: Retrieval may be faulty
- Check if enough documents are ingested
- Tune hybrid search parameters (`RAG_ALPHA`)

---

### Groundedness

**What it measures**: Whether claims in the answer are supported by the retrieved context.

**Score range**: 0.0 (unsupported) to 1.0 (fully supported)

**Target**: > 0.85

**How it's calculated**:
```python
# For each claim in the answer:
# "Is this claim supported by the context?"
# Percentage of supported claims
```

**Example**:
```
Context: "Neural networks have input, hidden, and 
output layers [1]."

Good Answer (score: 1.0):
"Neural networks consist of input, hidden, and 
output layers [1]."

Bad Answer (score: 0.5):
"Neural networks have 5-10 layers on average and 
use backpropagation for training [1]."
(Claim about "5-10 layers" not in context)
```

**When to investigate**:
- Score < 0.8: Model may be hallucinating
- Check FactChecker agent is working
- Review agent prompts for accuracy emphasis

---

## 📑 Citation Metrics

### Citation Coverage

**What it measures**: Percentage of claims with proper citations.

**Score range**: 0% to 100%

**Target**: > 90%

**How it's calculated**:
```python
# Count sentences/claims in answer
# Count sentences with citation markers [1], [2], etc.
# coverage = citations / total_sentences
```

**Example**:
```
Good (100% coverage):
"Neural networks learn from data [1]. They use 
backpropagation for training [2]."
(2 claims, 2 citations)

Bad (50% coverage):
"Neural networks learn from data [1]. They are 
widely used in AI applications."
(2 claims, 1 citation)
```

**Enforced by**: Guardrails output validation

---

### Citation Quality

**What it measures**: Validity and consistency of citation markers.

**Checks**:
- ✅ Citations are sequential: [1], [2], [3]
- ✅ No gaps: Don't skip from [1] to [3]
- ✅ Citations reference actual sources
- ✅ Citation format correct: `[1]` not `(1)` or `[1.]`

**Example**:
```
Good:
"Transformers use attention [1]. They process 
sequences in parallel [2]."

Bad:
"Transformers use attention [3]. They process 
sequences [1]."
(Non-sequential)
```

---

## 📝 Text Quality Metrics

### ROUGE Scores

**What it measures**: Overlap between generated summary and reference text.

**Types**:
- **ROUGE-1**: Unigram overlap
- **ROUGE-2**: Bigram overlap
- **ROUGE-L**: Longest common subsequence

**Score range**: 0.0 to 1.0

**Typical scores**:
- ROUGE-1: 0.3-0.5 (good)
- ROUGE-2: 0.1-0.3 (good)
- ROUGE-L: 0.3-0.4 (good)

**Use case**: Evaluate summarization quality against ground truth.

**Note**: Requires reference summaries (not always available).

---

### BLEU Score

**What it measures**: Precision of n-gram matches (originally for translation).

**Score range**: 0.0 to 1.0

**Typical scores**: 0.2-0.5 (good for summaries)

**Use case**: Translation quality (experimental in our system).

---

### Semantic Similarity

**What it measures**: Cosine similarity between answer and context embeddings.

**Score range**: 0.0 (unrelated) to 1.0 (identical)

**Target**: > 0.7

**How it's calculated**:
```python
# Embed answer and context
answer_vec = embedder.embed([answer])
context_vec = embedder.embed([context])

# Cosine similarity
similarity = cosine_similarity(answer_vec, context_vec)
```

**Use case**: Ensure answer is grounded in retrieved context.

---

## ⏱️ Performance Metrics

### Response Time

**What it measures**: Total time from request to response.

**Target**: < 30 seconds

**Breakdown**:
| Component | Time | Percentage |
|-----------|------|------------|
| Input validation | 10ms | <1% |
| Context retrieval | 500ms | 2% |
| Writer agent | 10s | 36% |
| Reviewer agent | 5s | 18% |
| FactChecker agent | 10s | 36% |
| Output validation | 20ms | <1% |
| **Total** | **~28s** | **100%** |

---

### Latency per Agent

**Writer Agent**: 8-12 seconds
- Drafts initial summary
- Longest because generates most text

**Reviewer Agent**: 4-6 seconds
- Reviews and improves existing text
- Shorter edits

**FactChecker Agent**: 8-12 seconds
- Validates claims against context
- Similar to Writer in complexity

---

### Ingestion Speed

**Per paper**: 4-6 seconds (CPU mode)

**Breakdown**:
| Step | Time | Percentage |
|------|------|------------|
| PDF download | Varies | - |
| Text extraction | 1-2s | 25% |
| Chunking | 100ms | 2% |
| Embedding | 2-3s | 50% |
| Weaviate write | 500ms | 10% |

**Optimization**: GPU acceleration reduces embedding time to ~0.5s

---

## 📈 Metric Thresholds

### Quality Gates

| Metric | Threshold | Action if Below |
|--------|-----------|-----------------|
| Answer Relevance | 0.7 | Flag for review |
| Context Relevance | 0.6 | Improve retrieval |
| Groundedness | 0.8 | Check for hallucinations |
| Citation Coverage | 85% | Enforce stricter validation |
| Response Time | 35s | Optimize or use GPU |

---

## 🔍 How to Interpret Metrics

### High Answer Relevance, Low Groundedness

**Interpretation**: Answer addresses query but invents facts.

**Solution**:
- Strengthen FactChecker agent
- Reduce LLM temperature
- Add more explicit prompts about staying grounded

---

### High Groundedness, Low Answer Relevance

**Interpretation**: Answer is factual but off-topic.

**Solution**:
- Improve context retrieval (adjust `RAG_ALPHA`)
- Review Writer agent prompt for focus

---

### Low Context Relevance

**Interpretation**: Retrieved documents aren't useful.

**Solution**:
- Increase `RAG_TOP_K` to retrieve more chunks
- Check if relevant documents are ingested
- Tune hybrid search parameters

---

## 📊 Viewing Metrics

### Current: Logs

Metrics are logged during processing:
```bash
# View logs
docker compose logs api | grep -i "metric\|score"

# Example output:
# INFO - answer_relevance: 0.89
# INFO - context_relevance: 0.82
# INFO - groundedness: 0.94
# INFO - processing_time: 28.4s
```

### Future: Dashboard

Planned features:
- Real-time metric visualization
- Historical trends
- Comparative analysis
- Export to CSV

---

## 📚 Related Documentation

- **[Evaluation Overview](README.md)** - Introduction to evaluation
- **[TruLens Setup](TRULENS.md)** - Enable TruLens
- **[Guardrails](GUARDRAILS.md)** - Configure validation

---

**[⬅ Back to Evaluation](README.md)**