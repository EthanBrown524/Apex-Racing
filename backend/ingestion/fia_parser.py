"""FIA stewards' decision parser via IBM Docling.

Docling extracts structured text + tables from FIA PDFs. We chunk that text
through ai.rag.upsert_chunks so it becomes RAG context for Granite explanations.

Run:
    python -m ingestion.fia_parser path/to/decision.pdf --race-id 42

Or, in code:
    parse_fia_pdf(pdf_path, race_id=42, title='Decision 47')
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ai.rag import chunk_for_storage, upsert_chunks
from db.connection import SessionLocal


def _docling_extract(pdf_path: Path) -> str:
    """Return the full plain-text content of a PDF using Docling.
    Falls back to a stub message if Docling or the file is unavailable so
    callers can keep going in a partial environment."""
    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document
        return doc.export_to_markdown()
    except ImportError:
        fallback = _pdfium_extract(pdf_path)
        if fallback:
            return fallback
        return f"(Docling not installed - install with `pip install docling`. Skipped {pdf_path.name}.)"
    except Exception as exc:
        fallback = _pdfium_extract(pdf_path)
        if fallback:
            return fallback
        return f"(Docling failed on {pdf_path.name}: {exc})"


def _pdfium_extract(pdf_path: Path) -> str:
    """Lightweight text fallback for PDFs Docling cannot parse cleanly."""
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(pdf_path))
        pages: list[str] = []
        for page in pdf:
            textpage = page.get_textpage()
            pages.append(textpage.get_text_range())
            textpage.close()
            page.close()
        pdf.close()
        return "\n\n".join(page.strip() for page in pages if page.strip())
    except Exception:
        return ""


def parse_fia_pdf(
    pdf_path: str | Path,
    race_id: int | None = None,
    title: str | None = None,
) -> dict:
    path = Path(pdf_path)
    if not path.exists():
        return {"ok": False, "error": f"File not found: {path}"}

    markdown = _docling_extract(path)
    chunks = chunk_for_storage(
        markdown,
        source="fia_decision",
        race_id=race_id,
        title=title or path.stem,
        path=str(path),
    )
    if not chunks:
        return {"ok": False, "error": "No text extracted"}

    with SessionLocal() as db:
        written = upsert_chunks(db, race_id=race_id, source="fia_decision", items=chunks)

    return {
        "ok": True,
        "race_id": race_id,
        "title": title or path.stem,
        "chunks": written,
        "preview": markdown[:400],
    }


def parse_fia_directory(directory: str | Path, race_id: int | None = None) -> list[dict]:
    """Process every *.pdf in a directory tree."""
    out = []
    root = Path(directory)
    for pdf in sorted(root.rglob("*.pdf")):
        out.append(parse_fia_pdf(pdf, race_id=race_id, title=pdf.stem))
    return out


def _main() -> None:
    parser = argparse.ArgumentParser(description="Parse FIA decisions into the RAG index.")
    parser.add_argument("path", help="PDF path or directory")
    parser.add_argument("--race-id", type=int, default=None)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_dir():
        results = parse_fia_directory(target, race_id=args.race_id)
        for r in results:
            print(r)
    else:
        print(parse_fia_pdf(target, race_id=args.race_id, title=args.title))


if __name__ == "__main__":
    _main()
