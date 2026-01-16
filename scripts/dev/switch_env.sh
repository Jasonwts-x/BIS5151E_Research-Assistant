#!/bin/bash
# Switch environment context between container and host

CONTEXT=$1

if [ -z "$CONTEXT" ]; then
    echo "Usage: $0 [container|host]"
    exit 1
fi

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found. Create it from .env.example first."
    exit 1
fi

if [ "$CONTEXT" = "container" ]; then
    echo "Switching to CONTAINER context..."
    sed -i 's|OLLAMA_HOST=http://localhost:11434|OLLAMA_HOST=http://ollama:11434|g' "$ENV_FILE"
    sed -i 's|WEAVIATE_URL=http://localhost:8080|WEAVIATE_URL=http://weaviate:8080|g' "$ENV_FILE"
    sed -i 's|POSTGRES_HOST=localhost|POSTGRES_HOST=postgres|g' "$ENV_FILE"
    echo "✅ Configured for container context"
elif [ "$CONTEXT" = "host" ]; then
    echo "Switching to HOST context..."
    sed -i 's|OLLAMA_HOST=http://ollama:11434|OLLAMA_HOST=http://localhost:11434|g' "$ENV_FILE"
    sed -i 's|WEAVIATE_URL=http://weaviate:8080|WEAVIATE_URL=http://localhost:8080|g' "$ENV_FILE"
    sed -i 's|POSTGRES_HOST=postgres|POSTGRES_HOST=localhost|g' "$ENV_FILE"
    echo "✅ Configured for host context"
else
    echo "❌ Invalid context. Use 'container' or 'host'."
    exit 1
fi

echo ""
echo "Current configuration:"
grep -E "(OLLAMA_HOST|WEAVIATE_URL|POSTGRES_HOST)" "$ENV_FILE"