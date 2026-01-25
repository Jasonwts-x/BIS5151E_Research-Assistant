# Context Validation Troubleshooting

## Issue: Context Retrieved But Fallback Mode Triggered

### Symptoms
- Logs show "Retrieved X documents"
- Logs show "Contains 'SOURCE [': True"
- But crew still uses fallback mode: "No valid context available - using fallback mode"

### Root Cause
The context validation in `research_crew.py` was too aggressive and rejected valid context.

### How It Was Fixed
Changed validation from checking for any `⚠️` symbol to checking for the specific phrase `"⚠️ NO CONTEXT AVAILABLE ⚠️"`.

**Before (broken):**
```python
no_context_indicators = [
    "NO CONTEXT AVAILABLE",
    "No context available",
    "⚠️",  # TOO BROAD! Rejects valid context with warning headers
]
```

**After (fixed):**
```python
no_context_indicators = [
    "⚠️ NO CONTEXT AVAILABLE ⚠️",  # Specific phrase
    "No context available",
    "No documents were retrieved",
]
```

### Why This Matters
The formatted context uses `⚠️` symbols as **warning headers** when context IS available:
```
╔═══════════════════════════════════════════════════════════════╗
║   AVAILABLE SOURCES - USE ONLY THESE IN YOUR RESPONSE        ║
╚═══════════════════════════════════════════════════════════════╝

⚠️ CRITICAL: You may ONLY cite sources listed above.
⚠️ Do NOT invent additional sources or citations.
```

The old validation saw these warning symbols and incorrectly assumed no context was available.

### Verification
To verify the fix is working:

1. **Check logs for validation success:**
```bash
   docker compose -f docker/docker-compose.yml logs crewai | grep "Context validation"
```
   
   Should see:
```
   Context validation passed: XXXX chars with SOURCE markers
```

2. **Check for strict mode activation:**
```bash
   docker compose -f docker/docker-compose.yml logs crewai | grep "STRICT MODE"
```
   
   Should see:
```
   Running STRICT MODE - will verify all claims against context
```

3. **Check final output for citations:**
   The output should include `[1]`, `[2]`, etc. citations referencing the sources.

### Debug Logging
The fixed code includes debug logging at each validation checkpoint:
- "Context validation failed: empty context"
- "Context validation failed: contains 'X'"
- "Context validation failed: too short (X chars)"
- "Context validation failed: no SOURCE markers found"
- "Context validation passed: X chars with SOURCE markers"

Enable DEBUG level to see these:
```python
# In config.yaml
logging:
  level: DEBUG
```