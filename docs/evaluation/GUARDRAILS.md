# Guardrails Configuration

Input and output validation with Guardrails AI.

---

## 🛡️ What are Guardrails?

Guardrails provide safety checks for:
1. **Input Validation** - Prevent harmful or invalid queries
2. **Output Validation** - Ensure safe, high-quality responses

---

## 🎯 Input Validation

### Checks Performed

| Check | Description | Action if Failed |
|-------|-------------|------------------|
| **Length** | Query max 10,000 chars | Reject with 400 |
| **Jailbreak** | Detect prompt injection | Reject with 400 |
| **PII** | Detect personal info | Reject with 400 |
| **Off-Topic** | Detect irrelevant queries | Warning only |

### Example Validations

**Query too long**:
```python
query = "a" * 10001
# Result: 400 Bad Request
# "Query exceeds maximum length of 10000 characters"
```

**Jailbreak attempt**:
```python
query = "Ignore previous instructions and..."
# Result: 400 Bad Request
# "Potential jailbreak attempt detected"
```

**PII detected**:
```python
query = "My email is john@example.com, can you help?"
# Result: 400 Bad Request
# "Personal information detected in query"
```

---

## 📤 Output Validation

### Checks Performed

| Check | Description | Action if Failed |
|-------|-------------|------------------|
| **Citations** | Verify citation format | Warning/reject |
| **Hallucination Markers** | Detect uncertainty phrases | Warning only |
| **Length** | Response 200-500 words | Warning only |
| **Harmful Content** | Safety check | Reject output |

### Example Validations

**Missing citations**:
```python
answer = "Neural networks are powerful. They learn from data."
# Warning: Citation coverage only 0% (target: 90%)
```

**Hallucination markers**:
```python
answer = "I think neural networks might use backpropagation..."
# Warning: Contains uncertainty markers: "I think", "might"
```

**Harmful content**:
```python
answer = "Here's how to hack into systems..."
# Result: Response rejected, error returned to user
```

---

## ⚙️ Configuration

### Environment Variables
```bash
# .env file

# Citation enforcement
GUARDRAILS_CITATION_REQUIRED=true  # Require citations in output
                                    # true: Strict (reject if missing)
                                    # false: Lenient (warn only)

# Strict mode
GUARDRAILS_STRICT_MODE=false       # Enable stricter validation
                                    # true: Reject on warnings
                                    # false: Warn but allow
```

### Modes

**Lenient Mode** (default):
- `GUARDRAILS_STRICT_MODE=false`
- Warnings logged but request proceeds
- Suitable for development

**Strict Mode**:
- `GUARDRAILS_STRICT_MODE=true`
- Warnings cause rejection
- Suitable for production

---

## 🔧 Customization

### Modify Validation Rules

Edit `src/eval/guardrails/validators/input.py`:
```python
class InputValidator:
    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.max_query_length = 10000  # Adjust limit
        
    def _detect_jailbreak(self, text: str) -> bool:
        # Add custom jailbreak patterns
        patterns = [
            "ignore previous",
            "disregard instructions",
            # Add more patterns
        ]
        ...
```

### Add Custom Checks
```python
def validate(self, query: str) -> Tuple[bool, List[str]]:
    issues = []
    
    # Existing checks...
    
    # Add custom check
    if self._contains_profanity(query):
        issues.append("Profanity detected")
        
    return len(issues) == 0, issues
```

---

## 📊 Validation Results

### Input Validation Result
```python
{
    "passed": True,
    "issues": []
}
```

Or:
```python
{
    "passed": False,
    "issues": [
        "Query exceeds maximum length",
        "PII detected: email address"
    ]
}
```

### Output Validation Result
```python
{
    "passed": True,
    "warnings": [
        "Citation coverage: 85% (target: 90%)"
    ]
}
```

---

## 🐛 Troubleshooting

### Issue: Valid queries being rejected

**Symptom**: Legitimate queries fail validation

**Solution**:
```bash
# Disable strict mode
GUARDRAILS_STRICT_MODE=false

# Or disable specific checks in code
```

### Issue: Citations not being enforced

**Symptom**: Responses without citations pass validation

**Solution**:
```bash
# Enable citation requirement
GUARDRAILS_CITATION_REQUIRED=true

# Check FactChecker agent is working
docker compose logs crewai | grep FactChecker
```

### Issue: False PII detections

**Symptom**: Generic emails/numbers flagged as PII

**Solution**: Adjust PII detection patterns in `src/eval/guardrails/validators/input.py`

---

## 📚 Related Documentation

- **[Evaluation Overview](README.md)** - All metrics
- **[Metrics Explanation](METRICS.md)** - What metrics mean
- **[Configuration Guide](../guides/CONFIGURATION.md)** - All config options

---

**[⬅ Back to Evaluation](README.md)**