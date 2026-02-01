-- ============================================================================
-- TruLens Custom Schema
-- ResearchAssistant Evaluation Tables
-- ============================================================================
-- This script runs second (02-*) and creates custom evaluation tables
-- NOTE: TruLens will create its own 'records' table on first initialization
-- Foreign key constraints will be added later via add-foreign-keys.sh
-- ============================================================================

-- Connect to trulens database
\c research_assistant

-- ============================================================================
-- CUSTOM PERFORMANCE METRICS SCHEMA
-- ============================================================================

-- Performance metrics table (supplement to TruLens records)
-- NOTE: Foreign key constraints will be added AFTER TruLens creates its tables
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
    language VARCHAR(10)
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
    sentence_count INTEGER
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
    warnings TEXT[]
);

CREATE INDEX IF NOT EXISTS idx_guardrails_record_id ON guardrails_results(record_id);
CREATE INDEX IF NOT EXISTS idx_guardrails_timestamp ON guardrails_results(timestamp);

-- ============================================================================
-- VIEWS FOR CONVENIENT QUERYING
-- ============================================================================

-- Create view only if records table exists (TruLens creates it on first use)
-- If it doesn't exist, skip silently without error
DO $$
BEGIN
    -- Check if records table exists
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'records'
    ) THEN
        -- Create view if records table exists
        CREATE OR REPLACE VIEW evaluation_summary AS
        SELECT 
            r.record_id,
            r.ts AS timestamp,
            r.input AS query,
            r.output AS answer,
            
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
        
        RAISE NOTICE 'evaluation_summary view created successfully';
    ELSE
        RAISE NOTICE 'records table does not exist yet - view will be created later';
        RAISE NOTICE 'Run: bash database/scripts/add-foreign-keys.sh after TruLens initializes';
    END IF;
END $$;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to add foreign key constraints after TruLens creates tables
CREATE OR REPLACE FUNCTION add_foreign_key_constraints()
RETURNS void AS $$
BEGIN
    -- Add FK constraint to performance_metrics if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_performance_record'
    ) THEN
        ALTER TABLE performance_metrics
        ADD CONSTRAINT fk_performance_record
        FOREIGN KEY(record_id) 
        REFERENCES records(record_id)
        ON DELETE CASCADE;
    END IF;
    
    -- Add FK constraint to quality_metrics if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_quality_record'
    ) THEN
        ALTER TABLE quality_metrics
        ADD CONSTRAINT fk_quality_record
        FOREIGN KEY(record_id) 
        REFERENCES records(record_id)
        ON DELETE CASCADE;
    END IF;
    
    -- Add FK constraint to guardrails_results if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_guardrails_record'
    ) THEN
        ALTER TABLE guardrails_results
        ADD CONSTRAINT fk_guardrails_record
        FOREIGN KEY(record_id) 
        REFERENCES records(record_id)
        ON DELETE CASCADE;
    END IF;
    
    RAISE NOTICE 'Foreign key constraints added successfully';
END;
$$ LANGUAGE plpgsql;

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
-- GRANTS
-- ============================================================================

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO research_assistant;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO research_assistant;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO research_assistant;

-- ============================================================================
-- COMPLETION LOG
-- ============================================================================

\echo '✅ TruLens schema initialized successfully!'
\echo ''
\echo 'Custom tables created:'
\echo '  - performance_metrics'
\echo '  - quality_metrics'
\echo '  - guardrails_results'
\echo ''
\echo 'Functions created:'
\echo '  - add_foreign_key_constraints()'
\echo '  - cleanup_old_records(days_to_keep)'
\echo ''
\echo '⚠️  IMPORTANT: After TruLens creates its tables, run:'
\echo '   bash database/scripts/add-foreign-keys.sh'
\echo '   This will add foreign key constraints and create the evaluation_summary view.'