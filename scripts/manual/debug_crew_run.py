#!/usr/bin/env python3
"""
Debug CrewAI workflow execution.
Run a single crew execution with verbose logging.

Usage:
    python scripts/manual/debug_crew_run.py "Your question here" [language]
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.agents.runner import CrewRunner


def main():
    """Run crew with debug logging."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    topic = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "en"
    
    print("=" * 70)
    print("CREW DEBUG RUN")
    print("=" * 70)
    print(f"Topic: {topic}")
    print(f"Language: {language}")
    print("=" * 70)
    print()
    
    try:
        # Create runner with monitoring
        print("Initializing CrewRunner...")
        runner = CrewRunner(
            enable_guardrails=True,
            enable_monitoring=False  # TruLens might not be installed
        )
        
        print("✅ Runner initialized")
        print()
        
        # Run workflow
        print("Executing crew workflow...")
        print("-" * 70)
        
        result = runner.run(topic=topic, language=language)
        
        print("-" * 70)
        print("✅ Workflow complete")
        print()
        
        # Display results
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        print(f"Topic: {result.topic}")
        print(f"Language: {result.language}")
        print(f"Context Documents: {len(result.context_docs)}")
        print()
        print("Final Output:")
        print("-" * 70)
        print(result.final_output)
        print("-" * 70)
        
        # Show context sources
        if result.context_docs:
            print()
            print("Context Sources:")
            print("-" * 70)
            sources = set()
            for doc in result.context_docs:
                source = doc.meta.get('source', 'unknown')
                sources.add(source)
            
            for i, source in enumerate(sorted(sources), 1):
                print(f"[{i}] {source}")
        
        print()
        print("=" * 70)
        print("DEBUG COMPLETE")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print("\n\n❌ ERROR")
        print("=" * 70)
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print()
        
        import traceback
        print("Traceback:")
        print("-" * 70)
        traceback.print_exc()
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()