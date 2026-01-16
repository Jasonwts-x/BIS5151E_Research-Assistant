#!/bin/bash
# Tail logs for all services or a specific one

cd "$(dirname "$0")/../.."

if [ -z "$1" ]; then
    echo "Tailing logs for all services..."
    docker compose -f docker/docker-compose.yml logs -f
else
    echo "Tailing logs for $1..."
    docker compose -f docker/docker-compose.yml logs -f "$1"
fi