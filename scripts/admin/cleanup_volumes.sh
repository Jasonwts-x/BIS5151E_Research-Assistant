#!/bin/bash
# Clean up all Docker volumes (WARNING: DESTRUCTIVE)

echo "⚠️  WARNING: This will delete ALL data!"
echo "   - Weaviate index"
echo "   - PostgreSQL database"
echo "   - n8n workflows"
echo "   - Ollama models"
echo ""
read -p "Continue? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

cd "$(dirname "$0")/../.."

echo "Stopping services..."
docker compose -f docker/docker-compose.yml down

echo "Removing volumes..."
docker compose -f docker/docker-compose.yml down -v

echo "✅ Cleanup complete"
echo ""
echo "To rebuild:"
echo "  docker compose -f docker/docker-compose.yml up -d"