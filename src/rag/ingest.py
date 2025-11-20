from __future__ import annotations

from pathlib import Path
from typing import List


def list_documents(data_dir: Path) -> List[Path]:
    """
    List all PDF and TXT files under data/raw.
    Returns a sorted list of Paths.
    """
    raw = data_dir / "raw"
    pdfs = sorted(raw.glob("*.pdf"))
    txts = sorted(raw.glob("*.txt"))
    return pdfs + txts


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    docs = list_documents(root / "data")
    names = [d.name for d in docs]
    print(f"Found {len(docs)} documents:", names)
