#!/bin/bash
# Backup all persistent data (Weaviate, PostgreSQL, n8n)
# Usage: ./backup_data.sh [backup_name]

set -e

BACKUP_NAME=${1:-"backup_$(date +%Y%m%d_%H%M%S)"}
BACKUP_DIR="backups/$BACKUP_NAME"

echo "Creating backup: $BACKUP_NAME"
mkdir -p "$BACKUP_DIR"

cd "$(dirname "$0")/../.."

# Backup Weaviate
echo "Backing up Weaviate..."
docker compose exec -T weaviate sh -c "tar czf - /var/lib/weaviate" > "$BACKUP_DIR/weaviate.tar.gz"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U n8n n8n > "$BACKUP_DIR/postgres.sql"

# Backup n8n workflows
echo "Backing up n8n workflows..."
cp -r docker/workflows "$BACKUP_DIR/workflows"

# Backup configuration
echo "Backing up configuration..."
cp configs/app.yaml "$BACKUP_DIR/app.yaml"
cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || true

echo "✅ Backup complete: $BACKUP_DIR"
echo ""
echo "To restore:"
echo "  ./scripts/admin/restore_data.sh $BACKUP_NAME"