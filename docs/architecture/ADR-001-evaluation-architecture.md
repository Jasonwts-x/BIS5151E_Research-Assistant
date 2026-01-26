# ADR 001: Evaluation Architecture

## Status
Accepted

## Context
Need comprehensive evaluation system for LLM application quality, safety, and performance monitoring.

## Decision
Implement evaluation as separate microservice with:
- TruLens for quality metrics
- Custom guardrails for safety
- Performance tracking
- PostgreSQL storage
- Streamlit dashboard

## Consequences

### Positive
- Isolated evaluation logic
- Independent scaling
- Clear separation of concerns
- Reusable across projects

### Negative
- Additional service complexity
- Network overhead
- Database dependency

## Alternatives Considered
1. In-process evaluation (rejected: couples services)
2. External SaaS (rejected: data privacy, cost)