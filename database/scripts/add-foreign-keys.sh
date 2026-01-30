#!/bin/bash
# Add foreign key constraints to custom tables after TruLens creates its tables
# Run this AFTER TruLens has created the 'records' table

set -e

echo "=========================================="
echo "Adding Foreign Key Constraints & Views"
echo "=========================================="
echo ""

# Check if postgres service is running
if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    echo "❌ postgres service is not running"
    echo "   Start it with: docker compose -f docker/docker-compose.yml up -d"
    exit 1
fi

echo "✅ postgres service is running"
echo ""

echo "Checking if TruLens 'records' table exists..."
TABLE_EXISTS=$(docker compose -f docker/docker-compose.yml exec -T postgres \
  psql -U research_assistant -d trulens -tAc \
  "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema='public' AND table_name='records');")

if [ "$TABLE_EXISTS" != "t" ]; then
    echo "❌ TruLens 'records' table does not exist yet"
    echo "   Run the evaluation service first to create TruLens tables"
    echo "   Then run this script again"
    exit 1
fi

echo "✅ TruLens 'records' table exists"
echo ""

echo "Adding foreign key constraints and creating views..."
docker compose -f docker/docker-compose.yml exec -T postgres \
  psql -U research_assistant -d trulens << 'EOF'

-- Add foreign key constraints
SELECT add_foreign_key_constraints();

-- Create evaluation_summary view
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

\echo ''
\echo '✅ evaluation_summary view created'

EOF

echo ""
echo "=========================================="
echo "✅ Foreign key constraints and views added!"
echo "=========================================="