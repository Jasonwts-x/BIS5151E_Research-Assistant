# Evaluation & Quality Monitoring

Documentation for quality assurance, metrics, and monitoring.

---

## 📚 Evaluation Documentation

| Document | Description |
|----------|-------------|
| **[METRICS.md](METRICS.md)** | Explanation of all quality metrics |
| **[TRULENS.md](TRULENS.md)** | TruLens setup and usage |
| **[GUARDRAILS.md](GUARDRAILS.md)** | Guardrails configuration and validation |
| **[DASHBOARD.md](DASHBOARD.md)** | Evaluation dashboard setup (future) |

---

## 🎯 Overview

ResearchAssistantGPT implements comprehensive evaluation to ensure high-quality outputs:

1. **Input Validation** (Guardrails) - Prevent harmful/invalid queries
2. **Output Validation** (Guardrails) - Ensure safe, high-quality responses
3. **RAG Quality** (TruLens) - Measure answer relevance, groundedness, context quality
4. **Performance Tracking** - Monitor response times and resource usage

---

## 📊 Evaluation Pipeline
```
User Query
    ↓
┌──────────────────────────┐
│ 1. Input Validation      │
│    (Guardrails)          │
│    - Length check        │
│    - Jailbreak detection │
│    - PII detection       │
│    - Off-topic check     │
└──────────────────────────┘
    ↓
Processing (RAG + Agents)
    ↓
┌──────────────────────────┐
│ 2. Output Validation     │
│    (Guardrails)          │
│    - Citation check      │
│    - Hallucination detect│
│    - Length validation   │
│    - Safety check        │
└──────────────────────────┘
    ↓
┌──────────────────────────┐
│ 3. Quality Metrics       │
│    (TruLens)             │
│    - Answer relevance    │
│    - Context relevance   │
│    - Groundedness        │
│    - ROUGE/BLEU          │
└──────────────────────────┘
    ↓
Response to User
```

---

## 🎯 Quality Metrics

### Automatic Metrics

| Metric | Tool | Target | Current |
|--------|------|--------|---------|
| **Answer Relevance** | TruLens | > 0.8 | Monitoring |
| **Context Relevance** | TruLens | > 0.7 | Monitoring |
| **Groundedness** | TruLens | > 0.85 | Monitoring |
| **Citation Coverage** | Guardrails | > 90% | ✅ Enforced |
| **Response Time** | Performance | < 30s | ✅ 28s avg |

### Manual Metrics (Future)

- User satisfaction scores
- Expert evaluation
- A/B testing results

---

## 🛡️ Guardrails

### Input Validation

**Checks**:
- ✅ Query length (max 10,000 chars)
- ✅ Jailbreak attempt detection
- ✅ PII detection (emails, phone numbers)
- ✅ Off-topic query detection

**Configuration**: `.env`
```bash
GUARDRAILS_CITATION_REQUIRED=true
GUARDRAILS_STRICT_MODE=false
```

See [GUARDRAILS.md](GUARDRAILS.md) for details.

### Output Validation

**Checks**:
- ✅ Citation format validation ([1], [2], etc.)
- ✅ Hallucination marker detection ("I think", "I believe")
- ✅ Length constraints (200-500 words)
- ✅ Harmful content filtering

---

## 📈 TruLens Monitoring

**Metrics Tracked**:
1. **Answer Relevance**: Does the answer address the query?
2. **Context Relevance**: Is retrieved context useful?
3. **Groundedness**: Are claims supported by context?

**Status**: Experimental (stub implementation)

**Setup**: See [TRULENS.md](TRULENS.md)

---

## 🎛️ Configuration

### Enable/Disable Evaluation
```bash
# .env file

# Guardrails (input/output validation)
GUARDRAILS_CITATION_REQUIRED=true  # Require citations
GUARDRAILS_STRICT_MODE=false        # Lenient mode

# TruLens (quality metrics)
EVAL_ENABLE_TRULENS=true            # Enable TruLens
EVAL_FAITHFULNESS_METRIC=trulens_groundedness

# Performance tracking
EVAL_ENABLE_PERFORMANCE=true        # Track timing
```

---

## 📊 Viewing Metrics

### Current (Logs)

Metrics are logged to console:
```
INFO - Guardrails: Input validation passed
INFO - Query processed in 28.4s
INFO - TruLens: answer_relevance=0.89, groundedness=0.92
```

### Future (Dashboard)

Planned: Web dashboard for visualization
- Real-time metrics
- Historical trends
- Quality scores over time

See [DASHBOARD.md](DASHBOARD.md) (future)

---

## 🔧 Troubleshooting

### Issue: Guardrails blocking valid queries

**Solution**:
```bash
# Relax validation
GUARDRAILS_STRICT_MODE=false
```

### Issue: TruLens metrics not appearing

**Solution**:
```bash
# Check TruLens is enabled
EVAL_ENABLE_TRULENS=true

# Check logs
docker compose logs api | grep TruLens
```

---

## 📚 Related Documentation

- **[Metrics Explanation](METRICS.md)** - What each metric means
- **[TruLens Setup](TRULENS.md)** - Enable TruLens monitoring
- **[Guardrails Config](GUARDRAILS.md)** - Configure validation
- **[API Documentation](../api/README.md)** - API reference

---

**[⬅ Back to Documentation](../README.md)**