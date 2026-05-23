"""Download and ingest FIA PDF source documents from a manifest.

The manifest is intentionally small and reviewable: each entry has a stable
id, an official FIA URL, and optional season/event metadata. Downloaded PDFs
are ignored by git; the manifest is the reproducible source of truth.

Run:
    python -m ingestion.fia_sources download
    python -m ingestion.fia_sources ingest
    python -m ingestion.fia_sources all
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import requests
from sqlalchemy import func, select

from ai.rag import chunk_for_storage, upsert_chunks
from db.connection import SessionLocal
from db.models import Race
from ingestion.fia_parser import _docling_extract, _pdfium_extract


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = BACKEND_DIR / "fia_pdf_manifest.json"
DEFAULT_OUT_DIR = BACKEND_DIR / "fia_pdfs"


def load_manifest(path: str | Path = DEFAULT_MANIFEST) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("FIA PDF manifest must be a JSON list")
    return items


def _safe_part(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def local_path_for(item: dict[str, Any], out_dir: str | Path = DEFAULT_OUT_DIR) -> Path:
    category = _safe_part(item.get("category", "documents"))
    season = _safe_part(item.get("season", "unknown"))
    event = item.get("event")
    parts = [Path(out_dir), category, season]
    if event:
        parts.append(_safe_part(event))
    filename = _safe_part(item["id"]) + ".pdf"
    return Path(*parts, filename)


def download_manifest(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    force: bool = False,
    ids: set[str] | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    items = _filter_items(load_manifest(manifest_path), ids=ids, category=category)
    results: list[dict[str, Any]] = []
    headers = {"User-Agent": "APEX-Racing-Records/0.1 (+FIA PDF ingestion)"}

    for item in items:
        dest = local_path_for(item, out_dir)
        if dest.exists() and not force:
            results.append({"id": item["id"], "ok": True, "status": "exists", "path": str(dest)})
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            response = requests.get(item["url"], headers=headers, timeout=60)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and not response.content.startswith(b"%PDF"):
                raise ValueError(f"response does not look like a PDF: {content_type}")
            dest.write_bytes(response.content)
            results.append(
                {
                    "id": item["id"],
                    "ok": True,
                    "status": response.status_code,
                    "bytes": len(response.content),
                    "path": str(dest),
                }
            )
        except Exception as exc:
            results.append({"id": item["id"], "ok": False, "error": str(exc), "url": item["url"]})

    return results


def _race_id_for_item(db, item: dict[str, Any]) -> int | None:
    season = item.get("season")
    round_number = item.get("round")
    if not season or not round_number:
        return None
    return db.scalar(
        select(Race.id).where(Race.season_year == int(season), Race.round == int(round_number))
    )


def ingest_manifest(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    ids: set[str] | None = None,
    category: str | None = None,
    skip_existing: bool = True,
) -> list[dict[str, Any]]:
    items = _filter_items(load_manifest(manifest_path), ids=ids, category=category)
    results: list[dict[str, Any]] = []

    with SessionLocal() as db:
        for index, item in enumerate(items, start=1):
            print(f"[{index}/{len(items)}] {item['id']}", flush=True)
            pdf_path = local_path_for(item, out_dir)
            if not pdf_path.exists():
                results.append({"id": item["id"], "ok": False, "error": "PDF not downloaded"})
                continue

            race_id = _race_id_for_item(db, item)
            source = "fia_decision" if item.get("category") == "decision_documents" else "fia_regulation"
            title = item.get("title") or item["id"]
            if skip_existing and _existing_chunks(db, source=source, title=title, race_id=race_id):
                results.append(
                    {"id": item["id"], "ok": True, "race_id": race_id, "source": source, "chunks": 0, "status": "exists"}
                )
                print(f"  already indexed: {title}", flush=True)
                continue

            if item.get("category") == "regulations":
                markdown = _pdfium_extract(pdf_path) or _docling_extract(pdf_path)
            else:
                markdown = _docling_extract(pdf_path)
            chunks = chunk_for_storage(
                markdown,
                source=source,
                race_id=race_id,
                title=title,
                path=str(pdf_path),
                url=item.get("url"),
                season=item.get("season"),
                round=item.get("round"),
                event=item.get("event"),
                document_type=item.get("document_type"),
            )
            if not chunks:
                results.append({"id": item["id"], "ok": False, "error": "No text extracted"})
                continue

            written = upsert_chunks(db, race_id=race_id, source=source, items=chunks)
            print(f"  wrote {written} chunks", flush=True)
            results.append(
                {
                    "id": item["id"],
                    "ok": True,
                    "race_id": race_id,
                    "source": source,
                    "chunks": written,
                }
            )

    return results


def _filter_items(
    items: list[dict[str, Any]],
    ids: set[str] | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    if ids:
        items = [item for item in items if item.get("id") in ids]
    if category:
        items = [item for item in items if item.get("category") == category]
    return items


def _existing_chunks(db, source: str, title: str, race_id: int | None) -> int:
    # SQLAlchemy model metadata exposes the JSON column as metadata_ to avoid
    # colliding with DeclarativeBase.metadata.
    from db.models import RaceEmbedding

    stmt = select(func.count(RaceEmbedding.id)).where(
        RaceEmbedding.metadata_["source"].astext == source,
        RaceEmbedding.metadata_["title"].astext == title,
    )
    if race_id is None:
        stmt = stmt.where(RaceEmbedding.race_id.is_(None))
    else:
        stmt = stmt.where(RaceEmbedding.race_id == race_id)
    return db.scalar(stmt) or 0


def _print_results(results: list[dict[str, Any]]) -> None:
    ok = sum(1 for r in results if r.get("ok"))
    print(f"{ok}/{len(results)} succeeded")
    for result in results:
        marker = "OK" if result.get("ok") else "FAIL"
        detail = result.get("path") or result.get("chunks") or result.get("error") or ""
        print(f"{marker:4} {result.get('id')}: {detail}")


def _main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest FIA PDF documents.")
    parser.add_argument("command", choices=["download", "ingest", "all"])
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--force", action="store_true", help="Re-download existing PDFs")
    parser.add_argument("--id", action="append", dest="ids", help="Only process this manifest id. Can be repeated.")
    parser.add_argument("--category", choices=["regulations", "decision_documents"])
    parser.add_argument("--no-skip-existing", action="store_true", help="Index documents even if their chunks already exist")
    args = parser.parse_args()
    ids = set(args.ids or [])

    if args.command in {"download", "all"}:
        print("Downloading FIA PDFs")
        _print_results(
            download_manifest(args.manifest, args.out_dir, force=args.force, ids=ids, category=args.category)
        )
    if args.command in {"ingest", "all"}:
        print("Ingesting FIA PDFs")
        _print_results(
            ingest_manifest(
                args.manifest,
                args.out_dir,
                ids=ids,
                category=args.category,
                skip_existing=not args.no_skip_existing,
            )
        )


if __name__ == "__main__":
    _main()
