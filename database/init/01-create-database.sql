-- ============================================================================
-- Database Initialization - Database Creation
-- ResearchAssistant PostgreSQL Setup
-- ============================================================================
-- This script runs first (01-*) and creates required databases
-- Executed by: postgres user during container initialization
-- ============================================================================

-- ============================================================================
-- RESEARCH ASSISTANT DATABASE (for n8n)
-- ============================================================================

-- Main database already created via POSTGRES_DB env var
-- Just grant permissions
GRANT ALL PRIVILEGES ON DATABASE research_assistant TO research_assistant;

-- ============================================================================
-- TRULENS DATABASE (for evaluation)
-- ============================================================================

-- Create TruLens database if it doesn't exist
SELECT 'CREATE DATABASE trulens'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trulens')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE trulens TO research_assistant;

-- ============================================================================
-- COMPLETION LOG
-- ============================================================================

\echo '✅ Database creation complete:'
\echo '   - research_assistant (n8n workflows)'
\echo '   - trulens (evaluation metrics)'
\echo ''
\echo 'Next: Loading TruLens schema...'