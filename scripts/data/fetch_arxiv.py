# scripts/fetch_arxiv.py
from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import List

import arxiv
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

ROOT = Path(__file__).resolve().parents[1]
DATA_ARXIV = ROOT / "data" / "arxiv"


def _slugify(text: str, max_len: int = 60) -> str:
    """
    Turn a paper title into a filesystem-friendly slug.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "paper"


def _download_pdf(url: str, out_path: Path) -> None:
    logger.info("Downloading %s -> %s", url, out_path)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)


def fetch_arxiv_pdfs(
    query: str,
    max_results: int = 10,
    out_dir: Path | None = None,
) -> List[Path]:
    """
    Search ArXiv and download PDFs into data/raw (by default).

    Returns a list of downloaded file paths.
    """
    out_dir = out_dir or DATA_ARXIV
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Searching ArXiv for query='%s' (max_results=%d)",
        query,
        max_results,
    )

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    downloaded: List[Path] = []

    for result in search.results():
        paper_id = result.get_short_id()  # e.g. 2401.12345
        title_slug = _slugify(result.title)
        filename = f"arxiv-{paper_id}-{title_slug}.pdf"
        target = out_dir / filename

        if target.exists():
            logger.info("Skipping existing file %s", target)
            downloaded.append(target)
            continue

        try:
            _download_pdf(result.pdf_url, target)
            downloaded.append(target)
        except Exception as exc:
            logger.warning("Failed to download %s: %s", result.pdf_url, exc)

    logger.info("Finished. Downloaded %d PDFs into %s", len(downloaded), out_dir)
    return downloaded


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch ArXiv PDFs into data/raw for RAG indexing."
    )
    parser.add_argument(
        "query",
        type=str,
        help="ArXiv search query, e.g. 'explainable AI' or 'llm retrieval'.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of papers to download (default: 10).",
    )

    args = parser.parse_args()
    fetch_arxiv_pdfs(query=args.query, max_results=args.max_results)


if __name__ == "__main__":
    main()

# ----------------------------------------------------------------------
# How to run:
# python scripts/fetch_arxiv.py "your search query" --max-results 5
# python -m src.rag.rag_mvp
# or
# python -m src.rag.rag_embed   # later, if/when you re-enable that
# ----------------------------------------------------------------------
