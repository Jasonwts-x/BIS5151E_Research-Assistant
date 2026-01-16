#!/bin/bash
# Stop all services

cd "$(dirname "$0")/../.."

echo "Stopping Research Assistant services..."
docker compose -f docker/docker-compose.yml down

echo "✅ Services stopped"