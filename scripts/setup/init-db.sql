-- ============================================================================
-- Database Initialization Script
-- ResearchAssistant Evaluation Database
-- ============================================================================

-- Create TruLens database if it doesn't exist
-- Note: This script runs as postgres user during container initialization

-- ============================================================================
-- TRULENS DATABASE
-- ============================================================================

-- TruLens will create its own tables when initialized
-- We just ensure the database exists

-- Check if trulens database exists, if not create it
SELECT 'CREATE DATABASE trulens'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trulens')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE trulens TO postgres;

-- ============================================================================
-- CUSTOM PERFORMANCE METRICS SCHEMA
-- ============================================================================

-- Connect to trulens database for custom tables
\c trulens

-- Performance metrics table (supplement to TruLens records)
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Timing breakdown
    total_time FLOAT,
    rag_retrieval_time FLOAT,
    agent_writer_time FLOAT,
    agent_reviewer_time FLOAT,
    agent_factchecker_time FLOAT,
    llm_inference_time FLOAT,
    guardrails_time FLOAT,
    evaluation_time FLOAT,
    
    -- Resource metrics
    memory_usage_mb FLOAT,
    token_count INTEGER,
    
    -- Metadata
    model_name VARCHAR(100),
    language VARCHAR(10),
    
    CONSTRAINT fk_record
        FOREIGN KEY(record_id) 
        REFERENCES records(record_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_performance_record_id ON performance_metrics(record_id);
CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp);

-- ============================================================================
-- CUSTOM QUALITY METRICS SCHEMA
-- ============================================================================

-- Quality metrics table (ROUGE, BLEU, etc.)
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
    
    CONSTRAINT fk_record
        FOREIGN KEY(record_id) 
        REFERENCES records(record_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_quality_record_id ON quality_metrics(record_id);
CREATE INDEX IF NOT EXISTS idx_quality_timestamp ON quality_metrics(timestamp);

-- ============================================================================
-- GUARDRAILS VALIDATION RESULTS
-- ============================================================================

-- Guardrails validation results table
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
    
    -- Violation details
    violations TEXT[],
    warnings TEXT[],
    
    CONSTRAINT fk_record
        FOREIGN KEY(record_id) 
        REFERENCES records(record_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_guardrails_record_id ON guardrails_results(record_id);
CREATE INDEX IF NOT EXISTS idx_guardrails_timestamp ON guardrails_results(timestamp);

-- ============================================================================
-- VIEWS FOR CONVENIENT QUERYING
-- ============================================================================

-- Comprehensive evaluation view (joins all metrics)
CREATE OR REPLACE VIEW evaluation_summary AS
SELECT 
    r.record_id,
    r.ts AS timestamp,
    r.input AS query,
    r.output AS answer,
    
    -- TruLens feedback scores (would need to join feedback_results)
    -- This is a simplified version - actual implementation would parse feedback_results
    
    -- Performance metrics
    p.total_time,
    p.rag_retrieval_time,
    p.llm_inference_time,
    
    -- Quality metrics
    q.rouge_1,
    q.rouge_2,
    q.bleu_score,
    q.semantic_similarity,
    q.factuality_score,
    q.citation_count,
    
    -- Guardrails
    g.overall_passed AS guardrails_passed,
    g.violations,
    
    -- Overall score calculation (simplified)
    (COALESCE(q.factuality_score, 0) + 
     COALESCE(q.semantic_similarity, 0)) / 2 AS overall_score

FROM records r
LEFT JOIN performance_metrics p ON r.record_id = p.record_id
LEFT JOIN quality_metrics q ON r.record_id = q.record_id
LEFT JOIN guardrails_results g ON r.record_id = g.record_id
ORDER BY r.ts DESC;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to clean up old records (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_records(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM records 
    WHERE ts < CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA / SEED (Optional)
-- ============================================================================

-- No seed data needed for evaluation tables

-- ============================================================================
-- GRANTS
-- ============================================================================

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- ============================================================================
-- COMPLETION LOG
-- ============================================================================

\echo 'TruLens database initialized successfully!'
\echo 'Custom tables created: performance_metrics, quality_metrics, guardrails_results'
\echo 'Views created: evaluation_summary'
\echo 'Functions created: cleanup_old_records'