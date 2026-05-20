"""Retrieval-Augmented context builder for Granite prompts.

Stores chunks in RaceEmbedding with the embedding column (Vector(1536)) and
optional metadata: source ('race_narrative' | 'fia_decision' | 'fastf1_notes'),
race_id, lap_range, and free-form text.

When pgvector is installed the lookup uses an ANN ORDER BY; otherwise we fall
back to in-Python cosine similarity over the candidate rows.
"""

from __future__ import annotations

from typing import Iterable

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ai.embeddings import LEGACY_DIM, chunk_text, cosine, embed_text, embed_texts
from db.connection import SessionLocal
from db.models import RaceEmbedding


TOP_K = 6
PER_RACE_FILTER = True


def upsert_chunks(
    db: Session,
    race_id: int | None,
    source: str,
    items: Iterable[str | dict],
) -> int:
    """Embed and store chunks. Each item is either a raw string or a dict
    {'text': ..., 'meta': {...}}. Returns the count of rows written."""
    payloads: list[dict] = []
    for item in items:
        if isinstance(item, str):
            payloads.append({"text": item, "meta": {}})
        else:
            payloads.append({"text": item.get("text", ""), "meta": item.get("meta", {})})

    payloads = [p for p in payloads if p["text"]]
    if not payloads:
        return 0

    texts = [p["text"] for p in payloads]
    vectors = embed_texts(texts, target_dim=LEGACY_DIM)

    written = 0
    for payload, vector in zip(payloads, vectors):
        metadata = {"source": source, **payload["meta"]}
        row = RaceEmbedding(
            race_id=race_id,
            content=payload["text"],
            embedding=vector,
            metadata_=metadata,
        )
        db.add(row)
        written += 1
    db.commit()
    return written


def _pgvector_available(db: Session) -> bool:
    try:
        result = db.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).first()
        return result is not None
    except Exception:
        return False


def retrieve(
    db: Session,
    query: str,
    race_id: int | None = None,
    top_k: int = TOP_K,
) -> list[dict]:
    """Return the top_k most relevant chunks with content + metadata."""
    if not query:
        return []
    query_vec = embed_text(query, target_dim=LEGACY_DIM)

    if _pgvector_available(db):
        sql = """
            SELECT id, race_id, content, metadata,
                   embedding <=> (:qvec)::vector AS distance
            FROM race_embeddings
            WHERE (:race_id IS NULL OR race_id = :race_id)
            ORDER BY embedding <=> (:qvec)::vector
            LIMIT :top_k
        """
        try:
            rows = db.execute(
                text(sql),
                {"qvec": query_vec, "race_id": race_id, "top_k": top_k},
            ).all()
            return [
                {
                    "id": row.id,
                    "race_id": row.race_id,
                    "content": row.content,
                    "metadata": row.metadata or {},
                    "score": float(1.0 - row.distance) if row.distance is not None else 0.0,
                }
                for row in rows
            ]
        except Exception:
            pass

    stmt = select(RaceEmbedding)
    if PER_RACE_FILTER and race_id is not None:
        stmt = stmt.where(RaceEmbedding.race_id == race_id)
    rows = db.execute(stmt.limit(2000)).scalars().all()

    scored = []
    for row in rows:
        emb = row.embedding
        if isinstance(emb, str):
            try:
                emb = [float(x) for x in emb.strip("[]").split(",") if x.strip()]
            except Exception:
                continue
        if not emb:
            continue
        score = cosine(query_vec, emb)
        scored.append((score, row))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {
            "id": row.id,
            "race_id": row.race_id,
            "content": row.content,
            "metadata": row.metadata_ or {},
            "score": score,
        }
        for score, row in scored[:top_k]
    ]


def build_race_context(race_id: int, query: str, top_k: int = TOP_K) -> dict:
    """Public entry point used by counterfactual / commentary / chat.
    Returns {'context': str, 'citations': [...]} - never raises."""
    try:
        with SessionLocal() as db:
            chunks = retrieve(db, query=query, race_id=race_id, top_k=top_k)
    except Exception as exc:
        return {
            "context": f"(RAG unavailable: {exc})",
            "citations": [],
        }

    if not chunks:
        return {
            "context": "(No indexed race documents found - run `python -m ingestion.embed_races`.)",
            "citations": [],
        }

    formatted = "\n\n".join(
        f"[{i + 1}] ({chunk['metadata'].get('source', 'unknown')}) {chunk['content']}"
        for i, chunk in enumerate(chunks)
    )
    citations = [
        {
            "index": i + 1,
            "source": chunk["metadata"].get("source", "unknown"),
            "title": chunk["metadata"].get("title")
            or chunk["metadata"].get("source", "unknown"),
            "race_id": chunk["race_id"],
            "score": round(chunk["score"], 3),
            "snippet": (chunk["content"][:240] + "...") if len(chunk["content"]) > 240 else chunk["content"],
        }
        for i, chunk in enumerate(chunks)
    ]
    return {"context": formatted, "citations": citations}


def chunk_for_storage(text: str, source: str, race_id: int | None = None, **meta) -> list[dict]:
    """Helper for ingestion scripts: split a long doc into chunk payloads ready
    to feed into upsert_chunks."""
    return [
        {"text": chunk, "meta": {"source": source, "race_id": race_id, **meta}}
        for chunk in chunk_text(text)
    ]
