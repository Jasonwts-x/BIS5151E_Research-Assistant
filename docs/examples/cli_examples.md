# CLI Examples

Command-line interface examples for ResearchAssistantGPT.

## Setup

All CLI commands use the `src.rag.cli` module:
```bash
# From project root
python -m src.rag.cli --help

# Or from devcontainer
docker compose exec devcontainer python -m src.rag.cli --help
```

---

## Available Commands

### Help
```bash
# Show all commands
python -m src.rag.cli --help

# Show command-specific help
python -m src.rag.cli ingest-local --help
python -m src.rag.cli ingest-arxiv --help
python -m src.rag.cli query --help
```

---

## Ingestion Commands

### 1. Ingest Local Files

**Ingest all files**:
```bash
python -m src.rag.cli ingest-local
```

**Ingest specific pattern**:
```bash
# Only PDFs
python -m src.rag.cli ingest-local --pattern "*.pdf"

# Only ArXiv papers
python -m src.rag.cli ingest-local --pattern "arxiv-*.pdf"

# Specific file
python -m src.rag.cli ingest-local --pattern "paper_2024_01.pdf"
```

**Expected output**:
```
INFO - Starting local file ingestion
INFO - Pattern: *.pdf
INFO - Found 5 files
INFO - Processing: paper1.pdf
INFO - Processing: paper2.pdf
...
INFO - Ingestion complete: 42 chunks ingested, 0 skipped
```

---

### 2. Ingest ArXiv Papers

**Basic ingestion**:
```bash
python -m src.rag.cli ingest-arxiv "machine learning" --max-results 5
```

**Advanced search**:
```bash
# Title search
python -m src.rag.cli ingest-arxiv 'ti:"neural networks"' --max-results 10

# Category search
python -m src.rag.cli ingest-arxiv "cat:cs.AI" --max-results 20

# Author search
python -m src.rag.cli ingest-arxiv "au:Hinton" --max-results 5

# Combined search
python -m src.rag.cli ingest-arxiv 'ti:"attention is all you need" AND au:Vaswani' --max-results 1
```

**Expected output**:
```
INFO - Fetching papers from ArXiv
INFO - Query: machine learning
INFO - Max results: 5
INFO - Found 5 papers
INFO - Downloading: arxiv-2401.12345v1.pdf
INFO - Downloading: arxiv-2401.12346v1.pdf
...
INFO - Ingestion complete: 127 chunks ingested
```

---

## Query Commands

### 3. Query RAG Index

**Basic query**:
```bash
python -m src.rag.cli query "What is machine learning?"
```

**With custom top-k**:
```bash
python -m src.rag.cli query "Explain neural networks" --top-k 10
```

**Expected output**:
```
INFO - Querying RAG pipeline
INFO - Query: What is machine learning?
INFO - Top-k: 5

Retrieved Documents:
---
SOURCE [1]: arxiv-2401.12345v1.pdf
Machine learning is a method of data analysis...

SOURCE [2]: paper_intro.txt
ML systems can learn from data...

---
Total: 5 documents retrieved
```

---

## Admin Commands

### 4. Reset Index

**Interactive reset** (asks for confirmation):
```bash
python -m src.rag.cli reset-index
```

**Output**:
```
WARNING - This will delete ALL documents from the index!
Current document count: 127
Are you sure? (yes/no): yes
INFO - Deleting collection...
INFO - Index reset complete
```

**Force reset** (no confirmation):
```bash
python -m src.rag.cli reset-index --yes
```

---

### 5. Show Statistics
```bash
python -m src.rag.cli stats
```

**Output**:
```
RAG Index Statistics
====================
Collection: ResearchDocument
Schema Version: 1.0.0
Document Count: 127
Status: Active
```

---

## Advanced Usage

### Pipeline Operations

**Full reset and re-index**:
```bash
#!/bin/bash
# Reset and rebuild index

echo "Resetting index..."
python -m src.rag.cli reset-index --yes

echo "Ingesting local files..."
python -m src.rag.cli ingest-local

echo "Ingesting ArXiv papers..."
python -m src.rag.cli ingest-arxiv "transformers" --max-results 10

echo "Checking stats..."
python -m src.rag.cli stats

echo "Done!"
```

---

### Batch Ingestion

**Ingest multiple topics**:
```bash
#!/bin/bash
# Ingest papers on multiple topics

topics=(
    "attention mechanisms"
    "transformer architecture"
    "retrieval augmented generation"
)

for topic in "${topics[@]}"; do
    echo "Ingesting: $topic"
    python -m src.rag.cli ingest-arxiv "$topic" --max-results 5
done

echo "Total documents:"
python -m src.rag.cli stats
```

---

### Test Retrieval Quality

**Query multiple times to test**:
```bash
#!/bin/bash
# Test retrieval with different queries

queries=(
    "What is machine learning?"
    "Explain neural networks"
    "How do transformers work?"
)

for query in "${queries[@]}"; do
    echo "================================"
    echo "Query: $query"
    echo "================================"
    python -m src.rag.cli query "$query" --top-k 3
    echo ""
done
```

---

## Docker Integration

### From Host (Windows PowerShell)
```powershell
# Run CLI inside devcontainer
docker compose exec devcontainer python -m src.rag.cli ingest-local

# Run CLI inside API container
docker compose exec api python -m src.rag.cli query "What is AI?"
```

### From Host (Linux/macOS)
```bash
# Run CLI inside devcontainer
docker compose exec devcontainer python -m src.rag.cli ingest-local

# Run CLI inside API container
docker compose exec api python -m src.rag.cli query "What is AI?"
```

---

## Troubleshooting

### Issue: "Collection does not exist"

**Error**:
```
RuntimeError: Collection 'ResearchDocument' does not exist in Weaviate!
```

**Solution**:
```bash
# Create index by ingesting at least one document
python -m src.rag.cli ingest-local
```

---

### Issue: "No files found"

**Error**:
```
INFO - Found 0 files
INFO - Ingestion complete: 0 chunks ingested
```

**Solution**:
```bash
# Check data directory
ls data/raw/

# Verify pattern
python -m src.rag.cli ingest-local --pattern "*"
```

---

### Issue: "Connection refused"

**Error**:
```
ConnectionError: Cannot connect to Weaviate at http://weaviate:8080
```

**Solution**:
```bash
# Check Weaviate is running
docker compose ps weaviate

# Check from inside container
docker compose exec devcontainer curl http://weaviate:8080/v1/.well-known/ready
```

---

## Environment Variables

**Configure via .env**:
```bash
# .env
WEAVIATE_URL=http://weaviate:8080
RAG_CHUNK_SIZE=350
RAG_CHUNK_OVERLAP=60
RAG_TOP_K=5
```

**Override at runtime**:
```bash
RAG_TOP_K=10 python -m src.rag.cli query "What is AI?"
```

---

## Best Practices

### 1. Always Check Stats After Ingestion
```bash
python -m src.rag.cli ingest-arxiv "topic" --max-results 10
python -m src.rag.cli stats  # Verify documents were added
```

### 2. Use Patterns for Selective Ingestion
```bash
# Good: Specific pattern
python -m src.rag.cli ingest-local --pattern "arxiv-2024-*.pdf"

# Bad: Ingest everything including test files
python -m src.rag.cli ingest-local
```

### 3. Test Queries Before Production
```bash
# Test retrieval quality
python -m src.rag.cli query "test query" --top-k 5

# Check if results are relevant before using in API
```

---

**[⬆ Back to Examples](README.md)**