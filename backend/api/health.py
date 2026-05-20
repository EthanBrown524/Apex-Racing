"""Health + diagnostics endpoint.

Used by the frontend About/Footer + by judges sanity-checking the demo:
shows row counts, Granite credential status, and pgvector extension state.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import (
    Circuit,
    Driver,
    LapTime,
    PitStop,
    Race,
    RaceEmbedding,
    Scenario,
    TelemetryPath,
)


router = APIRouter(prefix="/health", tags=["health"])


def _table_count(db: Session, model) -> int:
    try:
        return db.scalar(select(func.count()).select_from(model)) or 0
    except Exception:
        return -1


def _has_pgvector(db: Session) -> bool:
    try:
        return (
            db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
            is not None
        )
    except Exception:
        return False


@router.get("")
def health(db: Session = Depends(get_db)) -> dict:
    seasons_present = []
    try:
        rows = db.execute(
            select(Race.season_year, func.count(Race.id))
            .group_by(Race.season_year)
            .order_by(Race.season_year.asc())
        ).all()
        seasons_present = [{"year": r[0], "races": r[1]} for r in rows if r[0]]
    except Exception:
        pass

    counts = {
        "races": _table_count(db, Race),
        "drivers": _table_count(db, Driver),
        "circuits": _table_count(db, Circuit),
        "lap_times": _table_count(db, LapTime),
        "pit_stops": _table_count(db, PitStop),
        "telemetry_paths": _table_count(db, TelemetryPath),
        "race_embeddings": _table_count(db, RaceEmbedding),
        "scenarios": _table_count(db, Scenario),
    }

    granite_configured = bool(os.getenv("IBM_API_KEY")) and bool(
        os.getenv("WATSONX_PROJECT_ID")
    )

    embedding_sources: list[dict] = []
    try:
        rows = db.execute(
            text(
                "SELECT metadata->>'source' AS source, COUNT(*) AS n "
                "FROM race_embeddings WHERE metadata IS NOT NULL "
                "GROUP BY metadata->>'source'"
            )
        ).all()
        embedding_sources = [{"source": r.source or "unknown", "count": r.n} for r in rows]
    except Exception:
        pass

    return {
        "status": "ok",
        "counts": counts,
        "seasons": seasons_present,
        "pgvector_installed": _has_pgvector(db),
        "granite_configured": granite_configured,
        "embedding_sources": embedding_sources,
        "ingestion_complete": counts.get("lap_times", 0) > 1000
        and counts.get("races", 0) >= 18,
    }
