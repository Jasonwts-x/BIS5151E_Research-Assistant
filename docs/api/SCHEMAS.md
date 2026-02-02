# Request & Response Schemas

Complete API data models and schemas.

---

## 📋 Table of Contents

- [Request Models](#request-models)
- [Response Models](#response-models)
- [Data Types](#data-types)
- [Validation Rules](#validation-rules)

---

## 📤 Request Models

### ArXivIngestRequest
```json
{
  "query": "string",
  "max_results": 10
}
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| query | string | ✅ Yes | - | 1-1000 chars |
| max_results | integer | ❌ No | 10 | 1-100 |

**Example**:
```json
{
  "query": "machine learning",
  "max_results": 5
}
```

---

### LocalIngestRequest
```json
{
  "pattern": "string"
}
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| pattern | string | ❌ No | "*" | Valid glob pattern |

**Examples**:
```json
{"pattern": "*"}          // All files
{"pattern": "*.pdf"}      // PDF files only
{"pattern": "paper_*.txt"} // Specific pattern
```

---

### ResearchQueryRequest
```json
{
  "query": "string",
  "language": "en",
  "top_k": 5
}
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| query | string | ✅ Yes | - | 1-10,000 chars |
| language | string | ❌ No | "en" | en, de, fr, es |
| top_k | integer | ❌ No | 5 | 1-20 |

---

### RAGQueryRequest
```json
{
  "query": "string",
  "top_k": 5
}
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| query | string | ✅ Yes | - | 1-10,000 chars |
| top_k | integer | ❌ No | 5 | 1-20 |

---

## 📥 Response Models

### IngestResponse
```json
{
  "source": "arxiv",
  "documents_loaded": 3,
  "chunks_created": 142,
  "chunks_ingested": 142,
  "chunks_skipped": 0,
  "errors": [],
  "success": true,
  "duration_seconds": 45.3
}
```

| Field | Type | Description |
|-------|------|-------------|
| source | string | Source type ("arxiv" or "local") |
| documents_loaded | integer | Number of documents processed |
| chunks_created | integer | Total chunks generated |
| chunks_ingested | integer | Chunks successfully stored |
| chunks_skipped | integer | Duplicate chunks skipped |
| errors | array[string] | Error messages (if any) |
| success | boolean | Overall success status |
| duration_seconds | float | Total processing time |

---

### ResearchQueryResponse
```json
{
  "query": "string",
  "answer": "string",
  "sources": [
    {
      "index": 1,
      "source": "paper.pdf",
      "content": "string",
      "authors": ["Author 1"],
      "publication_date": "2024-01-15"
    }
  ],
  "language": "en",
  "processing_time": 28.4,
  "metrics": {
    "retrieval_time": 0.5,
    "writer_time": 10.2,
    "reviewer_time": 5.1,
    "factchecker_time": 10.3
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| query | string | Original query |
| answer | string | Generated answer with citations |
| sources | array[Source] | Retrieved source documents |
| language | string | Response language |
| processing_time | float | Total time (seconds) |
| metrics | object | Timing breakdown |

---

### Source Object
```json
{
  "index": 1,
  "source": "paper.pdf",
  "content": "string",
  "authors": ["Author 1", "Author 2"],
  "publication_date": "2024-01-15",
  "arxiv_id": "2401.12345"
}
```

| Field | Type | Description |
|-------|------|-------------|
| index | integer | Citation number [1], [2], etc. |
| source | string | Filename or identifier |
| content | string | Retrieved chunk content |
| authors | array[string] | Paper authors (if available) |
| publication_date | string | Publication date (ISO 8601) |
| arxiv_id | string | ArXiv ID (if from ArXiv) |

---

### RAGQueryResponse
```json
{
  "query": "string",
  "documents": [
    {
      "content": "string",
      "source": "string",
      "score": 0.89,
      "metadata": {}
    }
  ],
  "total_results": 5,
  "retrieval_time": 0.45
}
```

---

### StatsResponse
```json
{
  "total_documents": 15,
  "total_chunks": 642,
  "sources": ["paper1.pdf", "paper2.pdf"],
  "index_size_mb": 12.5,
  "last_ingestion": "2025-02-02T10:30:00Z"
}
```

---

### ErrorResponse
```json
{
  "detail": "Error message",
  "status_code": 400,
  "type": "ValidationError"
}
```

| Field | Type | Description |
|-------|------|-------------|
| detail | string | Error description |
| status_code | integer | HTTP status code |
| type | string | Error type (optional) |

---

## 🔢 Data Types

### Language Codes

| Code | Language |
|------|----------|
| `en` | English |
| `de` | German (Deutsch) |
| `fr` | French (Français) |
| `es` | Spanish (Español) |

---

### Source Types

| Type | Description |
|------|-------------|
| `arxiv` | ArXiv papers |
| `local` | Local files (PDF, TXT) |

---

## ✅ Validation Rules

### Query Validation
```python
# Length: 1-10,000 characters
min_length = 1
max_length = 10000

# Allowed characters: Any UTF-8
# No validation on content (handled by Guardrails)
```

---

### File Pattern Validation
```python
# Valid patterns
"*"           # All files
"*.pdf"       # PDF only
"paper_*.txt" # Specific pattern

# Invalid patterns
".." # Path traversal not allowed
"/" # Absolute paths not allowed
```

---

### Language Validation
```python
# Supported languages
allowed_languages = ["en", "de", "fr", "es"]

# Case insensitive
"EN" == "en"  # Valid
```

---

## 📚 Related Documentation

- **[API Endpoints](ENDPOINTS.md)** - All endpoints
- **[API Overview](README.md)** - Getting started
- **[Examples](../examples/BASIC_USAGE.md)** - Usage examples

---

**[⬅ Back to API Documentation](README.md)**