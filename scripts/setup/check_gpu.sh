#!/bin/bash
# Helper script to detect GPU and suggest appropriate compose command

echo "=========================================="
echo "GPU Detection Helper"
echo "=========================================="
echo ""

# Check for NVIDIA
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    nvidia-smi --query-gpu=name --format=csv,noheader
    echo ""
    echo "Recommended command:"
    echo "  docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d"
    exit 0
fi

# Check for AMD
if command -v rocm-smi &> /dev/null; then
    echo "✅ AMD GPU detected (ROCm)"
    rocm-smi --showproductname
    echo ""
    echo "Recommended command:"
    echo "  docker compose -f docker-compose.yml -f docker-compose.amd.yml up -d"
    echo ""
    echo "⚠️  Note: Verify your AMD GPU is supported by Ollama"
    exit 0
fi

# No GPU detected
echo "ℹ️  No GPU detected (or drivers not installed)"
echo ""
echo "Running on CPU (default):"
echo "  docker compose up -d"
echo ""
echo "To use GPU later:"
echo "  1. Install NVIDIA drivers + NVIDIA Container Toolkit, OR"
echo "  2. Install AMD ROCm drivers"
echo "  3. Re-run this script"