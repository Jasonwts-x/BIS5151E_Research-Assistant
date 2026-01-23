#!/bin/bash
# Rebuild Docker images from scratch (clears cache)
# Useful when dependencies change

set -e

cd "$(dirname "$0")/../.."

echo "⚠️  This will rebuild all Docker images from scratch"
echo "   This may take 10-20 minutes"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Stopping services..."
docker compose -f docker/docker-compose.yml down

echo "Removing old images..."
docker compose -f docker/docker-compose.yml build --no-cache

echo "Starting services..."
docker compose -f docker/docker-compose.yml up -d

echo "✅ Rebuild complete"
docker compose ps