#!/bin/bash
# Restart specific service(s)
# Usage: ./restart_service.sh api crewai

set -e
cd "$(dirname "$0")/../.."

if [ $# -eq 0 ]; then
    echo "Usage: $0 <service1> [service2 ...]"
    echo "Example: $0 api crewai"
    exit 1
fi

for service in "$@"; do
    echo "Restarting $service..."
    docker compose -f docker/docker-compose.yml restart "$service"
done

echo "✅ Services restarted"