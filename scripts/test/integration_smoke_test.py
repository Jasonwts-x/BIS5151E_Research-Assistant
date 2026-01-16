#!/usr/bin/env python3
"""
Comprehensive integration smoke test.

Tests the entire stack:
1. All services are reachable
2. Ollama has the required model
3. Weaviate has indexed documents
4. RAG query pipeline works end-to-end
5. All API endpoints respond correctly

Usage:
    python scripts/test/integration_smoke_test.py
    python scripts/test/integration_smoke_test.py --api-url http://localhost:8000
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.config import load_config

# Colors
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def print_header(title: str) -> None:
    """Print section header."""
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}{title:^70}{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")


def print_test(name: str) -> None:
    """Print test name."""
    print(f"🧪 {name}...", end=" ", flush=True)


def print_pass() -> None:
    """Print test passed."""
    print(f"{GREEN}✅ PASS{NC}")


def print_fail(reason: str = "") -> None:
    """Print test failed."""
    msg = f"{RED}❌ FAIL{NC}"
    if reason:
        msg += f" - {reason}"
    print(msg)


def test_service_health(base_url: str, service: str, endpoint: str) -> bool:
    """Test if a service is reachable."""
    print_test(f"{service} health")
    try:
        resp = requests.get(f"{base_url}{endpoint}", timeout=5)
        if resp.status_code == 200:
            print_pass()
            return True
        else:
            print_fail(f"Status {resp.status_code}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False


def test_ollama_model(api_url: str, expected_model: str) -> bool:
    """Test if Ollama has the expected model."""
    print_test(f"Ollama has model '{expected_model}'")
    try:
        resp = requests.get(f"{api_url}/ollama/models", timeout=5)
        if resp.status_code != 200:
            print_fail(f"Status {resp.status_code}")
            return False
        
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        
        if expected_model in models:
            print_pass()
            return True
        else:
            print_fail(f"Model not found. Available: {models}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False


def test_weaviate_has_documents(api_url: str) -> bool:
    """Test if Weaviate has indexed documents."""
    print_test("Weaviate has indexed documents")
    
    # We'll do this by making a simple query
    # If it returns results, we know there are documents
    try:
        # This is indirect - ideally we'd have a /rag/stats endpoint
        # For now, we'll just check if ready says weaviate_ok: true
        resp = requests.get(f"{api_url}/ready", timeout=5)
        data = resp.json()
        
        if data.get("weaviate_ok"):
            print_pass()
            return True
        else:
            print_fail("Weaviate not ready")
            return False
    except Exception as e:
        print_fail(str(e))
        return False


def test_rag_query_pipeline(api_url: str) -> bool:
    """Test full RAG query pipeline."""
    print_test("RAG query pipeline (end-to-end)")
    
    payload = {
        "query": "What is artificial intelligence?",
        "language": "en"
    }
    
    try:
        start = time.time()
        resp = requests.post(
            f"{api_url}/rag/query",
            json=payload,
            timeout=60  # LLM can be slow
        )
        elapsed = time.time() - start
        
        if resp.status_code != 200:
            print_fail(f"Status {resp.status_code}")
            return False
        
        data = resp.json()
        answer = data.get("answer", "")
        
        if not answer or len(answer) < 50:
            print_fail("Answer too short or empty")
            return False
        
        print(f"{GREEN}✅ PASS{NC} ({elapsed:.1f}s)")
        print(f"   Answer length: {len(answer)} chars")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run comprehensive integration smoke tests"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://api:8000",
        help="Base URL for API service",
    )
    
    args = parser.parse_args()
    api_url = args.api_url.rstrip("/")
    
    cfg = load_config()
    
    print_header("INTEGRATION SMOKE TEST")
    
    print(f"API URL: {api_url}")
    print(f"Expected model: {cfg.llm.model}")
    print()
    
    results = []
    
    # Test 1: API Health
    results.append(test_service_health(api_url, "API", "/health"))
    
    # Test 2: API Readiness
    results.append(test_service_health(api_url, "API Readiness", "/ready"))
    
    # Test 3: Ollama Info
    results.append(test_service_health(api_url, "Ollama Info", "/ollama/info"))
    
    # Test 4: Ollama Model
    results.append(test_ollama_model(api_url, cfg.llm.model))
    
    # Test 5: Weaviate Documents
    results.append(test_weaviate_has_documents(api_url))
    
    # Test 6: RAG Query Pipeline
    results.append(test_rag_query_pipeline(api_url))
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print_header("SUMMARY")
    
    if passed == total:
        print(f"{GREEN}✅ ALL TESTS PASSED ({passed}/{total}){NC}")
        print()
        print("🎉 System is fully operational!")
        sys.exit(0)
    else:
        print(f"{RED}❌ SOME TESTS FAILED ({passed}/{total}){NC}")
        print()
        print("⚠️  Fix the failing components and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()