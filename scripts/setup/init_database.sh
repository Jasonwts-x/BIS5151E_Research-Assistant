#!/bin/bash
# Initialize/reset the PostgreSQL database for n8n
# WARNING: This will drop and recreate the database, losing all data

set -e

# Load environment variables
if [ -f "docker/.env" ]; then
    export $(grep -v '^#' docker/.env | xargs)
else
    echo "❌ docker/.env not found. Create it from docker/.env.example"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "PostgreSQL Database Initialization"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will DROP and RECREATE the database!"
echo "   Database: ${POSTGRES_DB}"
echo "   User: ${POSTGRES_USER}"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Checking if postgres service is running..."

if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    echo -e "${RED}❌ postgres service is not running${NC}"
    echo "   Start it with: docker compose up -d postgres"
    exit 1
fi

echo -e "${GREEN}✅ postgres service is running${NC}"
echo ""

echo "Dropping existing database (if exists)..."
docker compose -f docker/docker-compose.yml exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" || true

echo "Creating fresh database..."
docker compose -f docker/docker-compose.yml exec -T postgres psql -U postgres -c "CREATE DATABASE ${POSTGRES_DB};"

echo "Granting privileges to user..."
docker compose -f docker/docker-compose.yml exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Database initialized successfully${NC}"
echo "=========================================="
echo ""
echo "Database: ${POSTGRES_DB}"
echo "User: ${POSTGRES_USER}"
echo ""
echo "⚠️  You may need to restart n8n:"
echo "   docker compose restart n8n"