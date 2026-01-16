#!/usr/bin/env python3
"""
Clear Python and model caches.

This script removes:
- pip cache
- HuggingFace cache
- Sentence-transformers cache
- Python __pycache__ directories
- .ruff_cache

Usage:
    python scripts/admin/clear_cache.py
    python scripts/admin/clear_cache.py --dry-run
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def get_size_mb(path: Path) -> float:
    """Get directory size in MB."""
    if not path.exists():
        return 0.0
    
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except (PermissionError, OSError):
        pass
    
    return total / (1024 * 1024)  # Convert to MB


def remove_dir(path: Path, dry_run: bool = False) -> tuple[bool, float]:
    """Remove directory and return (success, size_mb)."""
    if not path.exists():
        return False, 0.0
    
    size = get_size_mb(path)
    
    if dry_run:
        return True, size
    
    try:
        shutil.rmtree(path)
        return True, size
    except Exception as e:
        print(f"   ⚠️  Failed to remove {path}: {e}")
        return False, 0.0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clear Python and model caches"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    
    args = parser.parse_args()
    
    root = Path(__file__).resolve().parents[2]
    
    print("=" * 70)
    print("CACHE CLEANUP")
    print("=" * 70)
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE (no files will be deleted)")
    
    print()
    
    # Define cache directories
    caches = {
        "pip": root / ".pip_cache",
        "HuggingFace": root / ".hf_cache",
        "ruff": root / ".ruff_cache",
    }
    
    total_freed = 0.0
    
    # Remove each cache
    for name, path in caches.items():
        print(f"Checking {name} cache at {path.relative_to(root)}...")
        
        if path.exists():
            size = get_size_mb(path)
            print(f"   Current size: {size:.2f} MB")
            
            if args.dry_run:
                print(f"   Would remove: {size:.2f} MB")
                total_freed += size
            else:
                success, freed = remove_dir(path, dry_run=False)
                if success:
                    print(f"   ✅ Removed: {freed:.2f} MB")
                    total_freed += freed
                else:
                    print(f"   ❌ Failed to remove")
        else:
            print(f"   ℹ️  Cache doesn't exist")
        
        print()
    
    # Remove __pycache__ directories
    print("Checking __pycache__ directories...")
    pycache_dirs = list(root.rglob("__pycache__"))
    
    if pycache_dirs:
        pycache_size = sum(get_size_mb(p) for p in pycache_dirs)
        print(f"   Found {len(pycache_dirs)} __pycache__ directories ({pycache_size:.2f} MB)")
        
        if args.dry_run:
            print(f"   Would remove: {pycache_size:.2f} MB")
            total_freed += pycache_size
        else:
            removed_count = 0
            for pdir in pycache_dirs:
                success, freed = remove_dir(pdir, dry_run=False)
                if success:
                    removed_count += 1
                    total_freed += freed
            
            print(f"   ✅ Removed {removed_count} directories ({pycache_size:.2f} MB)")
    else:
        print(f"   ℹ️  No __pycache__ directories found")
    
    print()
    print("=" * 70)
    
    if args.dry_run:
        print(f"Would free: {total_freed:.2f} MB")
    else:
        print(f"✅ Freed: {total_freed:.2f} MB")
    
    print("=" * 70)


if __name__ == "__main__":
    main()