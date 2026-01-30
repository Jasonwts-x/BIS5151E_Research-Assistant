#!/bin/bash
# =============================================================================
# PostgreSQL Backup Script
# =============================================================================
# Backs up ONLY PostgreSQL databases (research_assistant + trulens)
# For full system backup (including Weaviate, n8n), use scripts/admin/backup_data.sh
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_ROOT="$PROJECT_ROOT/database/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME=${1:-"postgres_$TIMESTAMP"}
BACKUP_DIR="$BACKUP_ROOT/$BACKUP_NAME"

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
# PRE-FLIGHT CHECKS
# =============================================================================

echo "=========================================="
echo "PostgreSQL Database Backup"
echo "=========================================="
echo ""

# Check if postgres service is running
log_info "Checking PostgreSQL service status..."
cd "$PROJECT_ROOT"

if ! docker compose -f docker/docker-compose.yml ps postgres | grep -q "Up"; then
    log_error "PostgreSQL service is not running"
    echo "   Start it with: docker compose -f docker/docker-compose.yml up -d postgres"
    exit 1
fi

log_success "PostgreSQL service is running"

# Create backup directory
log_info "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# =============================================================================
# BACKUP DATABASES
# =============================================================================

echo ""
log_info "Backing up databases..."
echo ""

# Backup research_assistant database (n8n)
echo "  📦 Backing up research_assistant database..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    pg_dump -U research_assistant -d research_assistant \
    --clean --if-exists --create \
    > "$BACKUP_DIR/research_assistant.sql"

log_success "research_assistant database backed up"

# Backup trulens database
echo "  📦 Backing up trulens database..."
docker compose -f docker/docker-compose.yml exec -T postgres \
    pg_dump -U research_assistant -d trulens \
    --clean --if-exists --create \
    > "$BACKUP_DIR/trulens.sql"

log_success "trulens database backed up"

# =============================================================================
# BACKUP METADATA
# =============================================================================

echo ""
log_info "Creating backup metadata..."

cat > "$BACKUP_DIR/metadata.txt" << EOF
Backup Metadata
===============
Date: $(date)
Hostname: $(hostname)
PostgreSQL Version: $(docker compose -f docker/docker-compose.yml exec -T postgres psql -U postgres -tAc "SELECT version();")

Databases:
- research_assistant (n8n workflows)
- trulens (evaluation metrics)

Files:
- research_assistant.sql ($(du -h "$BACKUP_DIR/research_assistant.sql" | cut -f1))
- trulens.sql ($(du -h "$BACKUP_DIR/trulens.sql" | cut -f1))

To restore:
  bash database/scripts/restore-postgres.sh $BACKUP_NAME
EOF

log_success "Metadata created"

# =============================================================================
# COMPRESS (OPTIONAL)
# =============================================================================

echo ""
read -p "Compress backup? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Compressing backup..."
    cd "$BACKUP_ROOT"
    tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
    
    ORIGINAL_SIZE=$(du -sh "$BACKUP_NAME" | cut -f1)
    COMPRESSED_SIZE=$(du -sh "$BACKUP_NAME.tar.gz" | cut -f1)
    
    log_success "Backup compressed: $BACKUP_NAME.tar.gz"
    echo "   Original: $ORIGINAL_SIZE → Compressed: $COMPRESSED_SIZE"
    
    read -p "Remove uncompressed backup? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$BACKUP_NAME"
        log_success "Uncompressed backup removed"
    fi
fi

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "=========================================="
log_success "Backup complete!"
echo "=========================================="
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "To restore this backup:"
echo "  bash database/scripts/restore-postgres.sh $BACKUP_NAME"
echo ""