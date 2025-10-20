from pathlib import Path

def list_documents(data_dir: Path):
    """List all PDFs in data/raw."""
    return list((data_dir / "raw").glob("*.pdf"))

if __name__ == "__main__":
    docs = list_documents(Path(__file__).resolve().parents[2] / "data")
    print(f"Found {len(docs)} documents:", [d.name for d in docs])