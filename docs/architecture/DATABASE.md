# Database Architecture

Database schemas and design for ResearchAssistantGPT.

---

## 📋 Database Overview

The system uses two database technologies:

| Database | Technology | Purpose |
|----------|-----------|---------|
| **Weaviate** | Vector DB | Document chunks, embeddings, hybrid search |
| **PostgreSQL** | Relational DB | n8n workflows, TruLens metrics |

---

## 🔍 Weaviate Schema

### ResearchDocument Class

**Purpose**: Store document chunks with embeddings and metadata

**Schema Definition** (`src/rag/core/schema.py`):
```python
{
    "class": "ResearchDocument",
    "description": "Academic research documents chunked for RAG retrieval",
    "vectorizer": "none",  # We provide embeddings
    "properties": [
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Text content of the document chunk",
            "indexFilterable": True,
            "indexSearchable": True
        },
        {
            "name": "source",
            "dataType": ["text"],
            "description": "Source filename or identifier",
            "indexFilterable": True,
            "indexSearchable": True
        },
        {
            "name": "document_id",
            "dataType": ["text"],
            "description": "Unique identifier for the parent document",
            "indexFilterable": True
        },
        {
            "name": "chunk_index",
            "dataType": ["int"],
            "description": "Sequential index of this chunk within the document",
            "indexFilterable": True
        },
        {
            "name": "chunk_hash",
            "dataType": ["text"],
            "description": "Content hash for deduplication (SHA-256)",
            "indexFilterable": True
        },
        {
            "name": "total_chunks",
            "dataType": ["int"],
            "description": "Total number of chunks in the parent document",
            "indexFilterable": True
        },
        # ArXiv Metadata
        {
            "name": "authors",
            "dataType": ["text[]"],
            "description": "Document authors (if available)",
            "indexFilterable": True
        },
        {
            "name": "publication_date",
            "dataType": ["text"],
            "description": "Publication date (ISO 8601)",
            "indexFilterable": True
        },
        {
            "name": "abstract",
            "dataType": ["text"],
            "description": "Document abstract",
            "indexSearchable": True
        },
        {
            "name": "arxiv_id",
            "dataType": ["text"],
            "description": "ArXiv ID (if from ArXiv)",
            "indexFilterable": True
        },
        {
            "name": "categories",
            "dataType": ["text[]"],
            "description": "ArXiv categories",
            "indexFilterable": True
        },
        # Ingestion Metadata
        {
            "name": "ingestion_timestamp",
            "dataType": ["text"],
            "description": "When this chunk was ingested (ISO 8601)",
            "indexFilterable": True
        },
        {
            "name": "schema_version",
            "dataType": ["text"],
            "description": "Schema version for migrations",
            "indexFilterable": True
        }
    ]
}
```

### Vector Configuration

**Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Distance Metric**: Cosine similarity
- **Normalization**: L2 normalized

### Indexing Strategy

**BM25 Index** (lexical search):
- Fields: `content`, `source`, `abstract`
- Tokenization: Standard
- Language: Multi-lingual

**Vector Index** (HNSW):
- Algorithm: Hierarchical Navigable Small World
- Ef Construction: 128
- Max Connections: 64
- Fast approximate nearest-neighbor search

---

## 🐘 PostgreSQL Schema

### Database: `research_assistant` (n8n)

**Purpose**: Store n8n workflow data

**Tables** (managed by n8n):
- `execution_entity` - Workflow executions
- `workflow_entity` - Workflow definitions
- `credentials_entity` - Stored credentials
- `webhook_entity` - Webhook configurations
- ... (many more, managed by n8n)

**Schema**: Managed by n8n migrations

---

### Database: `trulens` (experimental)

**Purpose**: Store evaluation metrics

**Schema** (`database/init/02-trulens-schema.sql`):

#### Table: `trulens_records`
```sql
CREATE TABLE IF NOT EXISTS trulens_records (
    record_id VARCHAR(255) PRIMARY KEY,
    app_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Input/Output
    query TEXT,
    response TEXT,
    context TEXT,
    
    -- Metrics
    answer_relevance FLOAT,
    context_relevance FLOAT,
    groundedness FLOAT,
    overall_score FLOAT,
    
    -- Metadata
    model_name VARCHAR(255),
    latency_ms INTEGER,
    
    -- Indexes
    INDEX idx_timestamp (timestamp),
    INDEX idx_app_id (app_id)
);
```

#### Table: `quality_metrics`
```sql
CREATE TABLE IF NOT EXISTS quality_metrics (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ROUGE scores
    rouge_1 FLOAT,
    rouge_2 FLOAT,
    rouge_l FLOAT,
    
    -- BLEU score
    bleu_score FLOAT,
    
    -- Semantic similarity
    semantic_similarity FLOAT,
    
    -- Factuality
    factuality_score FLOAT,
    factuality_issues TEXT[],
    
    -- Citation metrics
    citation_count INTEGER,
    citation_quality FLOAT,
    
    -- Answer metrics
    answer_length INTEGER,
    sentence_count INTEGER,
    
    -- Indexes
    INDEX idx_quality_record_id (record_id),
    INDEX idx_quality_timestamp (timestamp)
);
```

#### Table: `guardrails_results`
```sql
CREATE TABLE IF NOT EXISTS guardrails_results (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Overall validation
    input_passed BOOLEAN,
    output_passed BOOLEAN,
    overall_passed BOOLEAN,
    
    -- Input validation details
    jailbreak_detected BOOLEAN DEFAULT FALSE,
    pii_detected BOOLEAN DEFAULT FALSE,
    off_topic_detected BOOLEAN DEFAULT FALSE,
    
    -- Output validation details
    citation_issues BOOLEAN DEFAULT FALSE,
    hallucination_markers BOOLEAN DEFAULT FALSE,
    length_violation BOOLEAN DEFAULT FALSE,
    harmful_content BOOLEAN DEFAULT FALSE,
    
    -- Indexes
    INDEX idx_guardrails_record_id (record_id),
    INDEX idx_guardrails_timestamp (timestamp)
);
```

---

## 💾 Data Storage Patterns

### Weaviate

**Write Pattern**: Batch inserts
```python
# Batch insert chunks
with document_store.client.batch as batch:
    for chunk in chunks:
        batch.add_data_object(
            data_object=chunk_data,
            class_name="ResearchDocument",
            vector=embedding
        )
```

**Read Pattern**: Hybrid search
```python
result = retriever.run(
    query=query,
    query_embedding=query_embedding,
    top_k=5
)
```

### PostgreSQL

**Write Pattern**: Transactional inserts
```sql
BEGIN;
INSERT INTO trulens_records (...) VALUES (...);
INSERT INTO quality_metrics (...) VALUES (...);
COMMIT;
```

**Read Pattern**: Time-series queries
```sql
SELECT * FROM trulens_records
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

---

## 🔄 Data Lifecycle

### Weaviate

**Creation**:
1. Document ingested
2. Chunks created
3. Embeddings generated
4. Objects created in Weaviate

**Deletion**:
```python
# Delete by document_id
client.batch.delete_objects(
    class_name="ResearchDocument",
    where={
        "path": ["document_id"],
        "operator": "Equal",
        "valueText": doc_id
    }
)
```

**Update**: Delete and re-insert (no in-place updates)

### PostgreSQL

**Retention**: Indefinite (user's choice)

**Cleanup**:
```sql
-- Delete old evaluation records (older than 90 days)
DELETE FROM trulens_records
WHERE timestamp < NOW() - INTERVAL '90 days';
```

---

## 📊 Query Patterns

### Weaviate Queries

**Hybrid Search**:
```graphql
{
  Get {
    ResearchDocument(
      hybrid: {
        query: "machine learning"
        alpha: 0.5
      }
      limit: 5
    ) {
      content
      source
      authors
      _additional {
        score
      }
    }
  }
}
```

**Metadata Filtering**:
```graphql
{
  Get {
    ResearchDocument(
      where: {
        path: ["publication_date"]
        operator: GreaterThan
        valueText: "2023-01-01"
      }
      limit: 10
    ) {
      content
      publication_date
    }
  }
}
```

### PostgreSQL Queries

**Evaluation Metrics**:
```sql
-- Average scores by day
SELECT 
    DATE(timestamp) as date,
    AVG(answer_relevance) as avg_relevance,
    AVG(groundedness) as avg_groundedness,
    COUNT(*) as queries
FROM trulens_records
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

**Quality Trends**:
```sql
-- Citation quality over time
SELECT 
    DATE(timestamp) as date,
    AVG(citation_quality) as avg_citation_quality,
    AVG(citation_count) as avg_citation_count
FROM quality_metrics
GROUP BY DATE(timestamp)
ORDER BY date DESC
LIMIT 30;
```

---

## 🔐 Security

### Weaviate

**Current**: Anonymous access (local deployment)
```yaml
AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
```

**Production** (future):
- API key authentication
- OIDC integration
- Role-based access

### PostgreSQL

**Current**: Password authentication
```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

**Production** (future):
- Strong passwords
- SSL/TLS connections
- Read-only users for queries
- Audit logging

---

## 💾 Backup & Recovery

### Weaviate Backup

**Manual Backup**:
```bash
# Backup to filesystem
curl -X POST http://localhost:8080/v1/backups/filesystem \
  -H 'Content-Type: application/json' \
  -d '{"id": "backup-2025-02-02"}'
```

**Restore**:
```bash
# Restore from backup
curl -X POST http://localhost:8080/v1/backups/filesystem/backup-2025-02-02/restore
```

### PostgreSQL Backup

**Backup**:
```bash
docker compose exec postgres pg_dump \
  -U research_assistant research_assistant > backup.sql
```

**Restore**:
```bash
cat backup.sql | docker compose exec -T postgres \
  psql -U research_assistant research_assistant
```

---

## 📈 Performance Optimization

### Weaviate

**Index Optimization**:
- HNSW parameters tuned for speed/accuracy tradeoff
- Batch size: 100 objects per batch
- Connection pooling

**Query Optimization**:
- Limit results (top_k = 5-10)
- Use filters to reduce search space
- Cache frequent queries (future)

### PostgreSQL

**Indexes**:
```sql
-- Time-series queries
CREATE INDEX idx_timestamp ON trulens_records(timestamp DESC);

-- Lookups by record_id
CREATE INDEX idx_record_id ON quality_metrics(record_id);
```

**Partitioning** (future):
```sql
-- Partition by month
CREATE TABLE trulens_records_2025_02 PARTITION OF trulens_records
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

---

## 📚 Related Documentation

- **[Architecture Overview](OVERVIEW.md)** - System design
- **[RAG Pipeline](RAG_PIPELINE.md)** - Pipeline details
- **[Services](SERVICES.md)** - Service configurations

---

**[⬅ Back to Architecture](README.md)**