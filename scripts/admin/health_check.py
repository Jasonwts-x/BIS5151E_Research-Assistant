#!/usr/bin/env python3
"""
Check health of all services and report status.
Useful for monitoring and debugging.
"""
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def check_service(name: str, url: str, expected_status: int = 200) -> bool:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def main():
    services = {
        "API Health": "http://localhost:8000/health",
        "API Ready": "http://localhost:8000/ready",
        "CrewAI": "http://localhost:8100/health",
        "Weaviate": "http://localhost:8080/v1/.well-known/ready",
        "Ollama": "http://localhost:11434/api/tags",
        "n8n": "http://localhost:5678/healthz/readiness",
    }
    
    print("=" * 60)
    print("SERVICE HEALTH CHECK")
    print("=" * 60)
    
    results = {name: check_service(name, url) for name, url in services.items()}
    
    print("\n" + "=" * 60)
    healthy = sum(results.values())
    total = len(results)
    
    if healthy == total:
        print(f"✅ All services healthy ({healthy}/{total})")
        sys.exit(0)
    else:
        print(f"⚠️  Some services unhealthy ({healthy}/{total})")
        sys.exit(1)

if __name__ == "__main__":
    main()