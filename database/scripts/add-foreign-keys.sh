#!/bin/bash
# Add foreign key constraints to custom tables after TruLens creates its tables
# Run this AFTER TruLens has created the 'records' table

set -e

echo "=========================================="
echo "Adding Foreign Key Constraints"
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

echo "Adding foreign key constraints..."
docker compose -f docker/docker-compose.yml exec -T postgres \
  psql -U research_assistant -d trulens -c "SELECT add_foreign_key_constraints();"

echo ""
echo "=========================================="
echo "✅ Foreign key constraints added!"
echo "=========================================="