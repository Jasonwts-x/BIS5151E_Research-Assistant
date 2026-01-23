#!/bin/bash
# Convenient startup script for development

set -e

cd "$(dirname "$0")/../.."

echo "Starting Research Assistant services..."
echo ""

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected - using GPU acceleration"
    docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d
elif command -v rocm-smi &> /dev/null; then
    echo "🎮 AMD GPU detected - using GPU acceleration"
    docker compose -f docker/docker-compose.yml -f docker/docker-compose.amd.yml up -d
else
    echo "💻 No GPU detected - using CPU"
    docker compose -f docker/docker-compose.yml up -d
fi

echo ""
echo "✅ Services starting..."
echo ""
echo "Monitor logs with:"
echo "  docker compose -f docker/docker-compose.yml logs -f"
echo ""
echo "Access points:"
echo "  API: http://localhost:8000"
echo "  n8n: http://localhost:5678"
echo "  Weaviate: http://localhost:8080"