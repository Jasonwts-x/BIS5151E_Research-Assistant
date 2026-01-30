#!/bin/bash
# =============================================================================
# PostgreSQL Restore Script
# =============================================================================
# Restores ONLY PostgreSQL databases (research_assistant + trulens)
# WARNING: This will DROP and RECREATE databases, losing all current data!
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_ROOT="$PROJECT_ROOT/database/backups"
BACKUP_NAME="$1"

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

show_usage() {
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    if [ -d "$BACKUP_ROOT" ]; then
        ls -1 "$BACKUP_ROOT" | grep -E "^postgres_|\.tar\.gz$" || echo "  (none)"
    else
        echo "  (none)"
    fi
    echo ""
    exit 1
}

# =============================================================================
# VALIDATION
# =============================================================================

echo "=========================================="
echo "PostgreSQL Database Restore"
echo "=========================================="
echo ""

# Check if backup name provided
if [ -z "$BACKUP_NAME" ]; then
    log_error "No backup name provided"
    echo ""
    show_usage
fi

# Remove .tar.gz extension if provided
BACKUP_NAME="${BACKUP_NAME%.tar.gz}"

# Check if backup exists
BACKUP_DIR="$BACKUP_ROOT/$BACKUP_NAME"

if [ ! -d "$BACKUP_DIR" ]; then
    # Check if compressed backup exists
    if [ -f "$BACKUP_ROOT/$BACKUP_NAME.tar.gz" ]; then
        log_info "Found compressed backup, extracting..."
        cd "$BACKUP_ROOT"
        tar -xzf "$BACKUP_NAME.tar.gz"
        log_success "Backup extracted"
    else
        log_error "Backup not found: $BACKUP_NAME"
        echo ""
        show_usage
    fi
fi

# Check if postgres service is running
log_info "Checking PostgreSQL service status..."
cd "$PROJECT_ROOT"

if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    log_error "PostgreSQL service is not running"
    echo "   Start it with: docker compose -f docker/docker-compose.yml up -d postgres"
    exit 1
fi

log_success "PostgreSQL service is running"

# =============================================================================
# CONFIRMATION
# =============================================================================

echo ""
log_warning "WARNING: This will DROP and RECREATE databases!"
log_warning "All current data will be LOST!"
echo ""
echo "Backup to restore: $BACKUP_NAME"
echo "Backup location: $BACKUP_DIR"
echo ""

if [ -f "$BACKUP_DIR/metadata.txt" ]; then
    log_info "Backup metadata:"
    cat "$BACKUP_DIR/metadata.txt" | head -n 10
    echo ""
fi

read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    log_warning "Restore cancelled"
    exit 0
fi

# =============================================================================
# STOP DEPENDENT SERVICES
# =============================================================================

echo ""
log_info "Stopping dependent services..."

docker compose -f docker/docker-compose.yml stop n8n eval api crewai 2>/dev/null || true

log_success "Services stopped"

# =============================================================================
# RESTORE DATABASES
# =============================================================================

echo ""
log_info "Restoring databases..."
echo ""

# Restore research_assistant database
if [ -f "$BACKUP_DIR/research_assistant.sql" ]; then
    echo "  📦 Restoring research_assistant database..."
    
    # Drop existing connections
    docker compose -f docker/docker-compose.yml exec -T postgres \
        psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'research_assistant';" \
        2>/dev/null || true
    
    # Restore database
    docker compose -f docker/docker-compose.yml exec -T postgres \
        psql -U postgres < "$BACKUP_DIR/research_assistant.sql"
    
    log_success "research_assistant database restored"
else
    log_warning "research_assistant.sql not found in backup, skipping"
fi

# Restore trulens database
if [ -f "$BACKUP_DIR/trulens.sql" ]; then
    echo "  📦 Restoring trulens database..."
    
    # Drop existing connections
    docker compose -f docker/docker-compose.yml exec -T postgres \
        psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'trulens';" \
        2>/dev/null || true
    
    # Restore database
    docker compose -f docker/docker-compose.yml exec -T postgres \
        psql -U postgres < "$BACKUP_DIR/trulens.sql"
    
    log_success "trulens database restored"
else
    log_warning "trulens.sql not found in backup, skipping"
fi

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
log_success "Restore complete!"
echo "=========================================="
echo ""
echo "Databases restored from: $BACKUP_NAME"
echo ""
echo "Services restarted. Check logs with:"
echo "  docker compose -f docker/docker-compose.yml logs -f"
echo ""