#!/bin/bash
# =============================================================================
# Database Initialization Script
# =============================================================================
# Initialize/reset the PostgreSQL databases (research_assistant + trulens)
# WARNING: This will DROP and RECREATE databases, losing all data!
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# =============================================================================
# LOAD ENVIRONMENT VARIABLES
# =============================================================================

if [ -f "$PROJECT_ROOT/docker/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/docker/.env" | xargs)
    log_success "Environment variables loaded from docker/.env"
else
    log_error "docker/.env not found. Create it from docker/.env.example"
    exit 1
fi

# =============================================================================
# DISPLAY WARNING
# =============================================================================

echo "=========================================="
echo "PostgreSQL Database Initialization"
echo "=========================================="
echo ""
log_warning "WARNING: This will DROP and RECREATE databases!"
log_warning "All current data will be LOST!"
echo ""
echo "Databases to recreate:"
echo "  - ${POSTGRES_DB} (n8n workflows)"
echo "  - trulens (evaluation metrics)"
echo ""
echo "Database user: ${POSTGRES_USER}"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    log_warning "Database initialization cancelled"
    exit 0
fi

# =============================================================================
# CHECK POSTGRES SERVICE
# =============================================================================

echo ""
log_info "Checking PostgreSQL service status..."

cd "$PROJECT_ROOT"

if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    log_error "PostgreSQL service is not running"
    echo "   Start it with: docker compose -f docker/docker-compose.yml up -d postgres"
    exit 1
fi

log_success "PostgreSQL service is running"

# =============================================================================
# STOP DEPENDENT SERVICES
# =============================================================================

echo ""
log_info "Stopping dependent services (n8n, eval, api, crewai)..."

docker compose -f docker/docker-compose.yml stop n8n eval api crewai 2>/dev/null || true

log_success "Dependent services stopped"

# =============================================================================
# DROP EXISTING DATABASES
# =============================================================================

echo ""
log_info "Dropping existing databases..."

# Drop research_assistant database
echo "  🗑️  Dropping ${POSTGRES_DB} database..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" 2>/dev/null || true

# Drop trulens database
echo "  🗑️  Dropping trulens database..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres -c "DROP DATABASE IF EXISTS trulens;" 2>/dev/null || true

log_success "Existing databases dropped"

# =============================================================================
# CREATE FRESH DATABASES
# =============================================================================

echo ""
log_info "Creating fresh databases from init scripts..."

# Run 01-create-databases.sql
echo "  📦 Running 01-create-databases.sql..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres < "$PROJECT_ROOT/database/init/01-create-databases.sql"

# Run 02-trulens-schema.sql
echo "  📦 Running 02-trulens-schema.sql..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres < "$PROJECT_ROOT/database/init/02-trulens-schema.sql"

log_success "Databases initialized from init scripts"

# =============================================================================
# VERIFICATION
# =============================================================================

echo ""
log_info "Verifying database creation..."

# List databases
echo ""
echo "Databases in PostgreSQL:"
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U postgres -c "\l" | grep -E "research_assistant|trulens" || true

# List tables in trulens
echo ""
echo "Tables in trulens database:"
docker compose -f docker/docker-compose.yml exec -T postgres \
    psql -U research_assistant -d trulens -c "\dt" 2>/dev/null || echo "  (none yet - TruLens will create them on first use)"

# =============================================================================
# RESTART SERVICES
# =============================================================================

echo ""
log_info "Restarting services..."

docker compose -f docker/docker-compose.yml up -d n8n eval api crewai

log_success "Services restarted"

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "=========================================="
log_success "Database initialization complete!"
echo "=========================================="
echo ""
echo "Databases created:"
echo "  - ${POSTGRES_DB} (n8n workflows)"
echo "  - trulens (evaluation metrics)"
echo ""
echo "Custom tables created:"
echo "  - performance_metrics"
echo "  - quality_metrics"
echo "  - guardrails_results"
echo ""
log_warning "IMPORTANT: After TruLens creates its 'records' table, run:"
echo "  bash database/scripts/add-foreign-keys.sh"
echo ""
echo "Services should be starting. Check logs with:"
echo "  docker compose -f docker/docker-compose.yml logs -f"
echo ""