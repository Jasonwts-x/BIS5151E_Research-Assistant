#!/usr/bin/env python3
"""
Verify Ollama connectivity and model availability.
Run from devcontainer or api service.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from ollama import chat, list as ollama_list

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import load_config


def check_ollama_health(base_url: str) -> bool:
    """Check if Ollama service is reachable."""
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Ollama health check failed: {e}")
        return False


def check_models_available(expected_model: str) -> bool:
    """Check if expected model is available."""
    try:
        models = ollama_list()
        model_names = [m["name"] for m in models.get("models", [])]
        
        print(f"\n📋 Available models: {model_names}")
        
        if expected_model in model_names:
            print(f"✅ Model '{expected_model}' is available")
            return True
        else:
            print(f"❌ Model '{expected_model}' not found")
            return False
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return False


def test_simple_inference(model: str) -> bool:
    """Test basic inference capability."""
    try:
        print(f"\n🧪 Testing inference with model '{model}'...")
        response = chat(
            model=model,
            messages=[{"role": "user", "content": "Say 'Hello' in one word."}],
        )
        content = response.message.content.strip()
        print(f"✅ Inference test successful. Response: {content}")
        return True
    except Exception as e:
        print(f"❌ Inference test failed: {e}")
        return False


def main():
    """Run all Ollama verification checks."""
    print("=" * 70)
    print("OLLAMA CONNECTIVITY & MODEL VERIFICATION")
    print("=" * 70)
    
    cfg = load_config()
    base_url = cfg.llm.host
    model = cfg.llm.model
    
    print(f"\n📍 Configuration:")
    print(f"   Ollama Host: {base_url}")
    print(f"   Expected Model: {model}")
    
    # Check 1: Health
    print(f"\n🔍 Check 1: Ollama Service Health")
    health_ok = check_ollama_health(base_url)
    
    if not health_ok:
        print("\n❌ Ollama service is not reachable. Check docker-compose logs.")
        sys.exit(1)
    
    print("✅ Ollama service is healthy")
    
    # Check 2: Model availability
    print(f"\n🔍 Check 2: Model Availability")
    model_ok = check_models_available(model)
    
    if not model_ok:
        print(f"\n⚠️  Model '{model}' not found. Run: docker compose up ollama-init")
        sys.exit(1)
    
    # Check 3: Inference
    print(f"\n🔍 Check 3: Simple Inference Test")
    inference_ok = test_simple_inference(model)
    
    if not inference_ok:
        print("\n❌ Inference test failed")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✅ ALL CHECKS PASSED - Ollama is properly configured!")
    print("=" * 70)


if __name__ == "__main__":
    main()