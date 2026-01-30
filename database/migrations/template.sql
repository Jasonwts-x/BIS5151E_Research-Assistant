-- =============================================================================
-- Migration Template
-- =============================================================================
-- Filename: YYYY-MM-DD_description.sql
-- Description: [Brief description of what this migration does]
-- Author: [Your name]
-- Date: [YYYY-MM-DD]
-- =============================================================================

-- Connect to the appropriate database
\c trulens

-- =============================================================================
-- CHANGES
-- =============================================================================

-- Example: Add new column
-- ALTER TABLE performance_metrics ADD COLUMN IF NOT EXISTS new_column VARCHAR(100);

-- Example: Create new table
-- CREATE TABLE IF NOT EXISTS new_table (
--     id SERIAL PRIMARY KEY,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Example: Add index
-- CREATE INDEX IF NOT EXISTS idx_new_column ON performance_metrics(new_column);

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify changes
-- \d performance_metrics

-- =============================================================================
-- ROLLBACK (DOCUMENT ONLY - EXECUTE MANUALLY IF NEEDED)
-- =============================================================================

-- To rollback this migration:
-- ALTER TABLE performance_metrics DROP COLUMN IF EXISTS new_column;

-- =============================================================================
-- COMPLETION LOG
-- =============================================================================

\echo '✅ Migration complete: [description]'
```

### **database/backups/.gitkeep**
```
# Database backups directory
# Files in this directory are excluded from git (see .gitignore)