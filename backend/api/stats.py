"""Stats endpoint - the scale showcase.

Returns the rich numbers that the /stats page renders as animated heroes.
Designed to never error: any failed query returns 0 for its row, so the
page always paints something even on a half-populated DB.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import (
    Circuit,
    Constructor,
    Driver,
    LapTime,
    PitStop,
    Race,
    RaceEmbedding,
    RaceResult,
    SafetyCar,
    Scenario,
    TelemetryPath,
)


router = APIRouter(prefix="/stats", tags=["stats"])


YEARS_TARGET = [2019, 2020, 2021, 2022, 2023, 2024]
EXPECTED_RACES_PER_SEASON = 22  # rough average, used for the progress bar


def _safe_count(db: Session, model) -> int:
    try:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)
    except Exception:
        return 0


def _safe_scalar(db: Session, stmt) -> int:
    try:
        return int(db.scalar(stmt) or 0)
    except Exception:
        return 0


@router.get("")
def stats(db: Session = Depends(get_db)) -> dict:
    races = _safe_count(db, Race)
    drivers = _safe_count(db, Driver)
    constructors = _safe_count(db, Constructor)
    circuits = _safe_count(db, Circuit)
    lap_times = _safe_count(db, LapTime)
    pit_stops = _safe_count(db, PitStop)
    safety_cars = _safe_count(db, SafetyCar)
    telemetry_rows = _safe_count(db, TelemetryPath)
    race_results = _safe_count(db, RaceResult)
    embeddings = _safe_count(db, RaceEmbedding)
    scenarios = _safe_count(db, Scenario)

    telemetry_points = 0
    try:
        rows = db.execute(
            text("SELECT path FROM telemetry_paths WHERE path IS NOT NULL LIMIT 5000")
        ).all()
        sampled = sum(len(r.path or []) for r in rows)
        if rows:
            avg = sampled / len(rows)
            telemetry_points = int(avg * telemetry_rows)
    except Exception:
        telemetry_points = 0

    total_data_points = lap_times + pit_stops + race_results + telemetry_points

    season_breakdown = []
    try:
        rows = db.execute(
            select(Race.season_year, func.count(Race.id))
            .where(Race.season_year.in_(YEARS_TARGET))
            .group_by(Race.season_year)
            .order_by(Race.season_year.asc())
        ).all()
        per_year = {row[0]: row[1] for row in rows if row[0]}
    except Exception:
        per_year = {}

    for year in YEARS_TARGET:
        ingested = per_year.get(year, 0)
        season_breakdown.append(
            {
                "year": year,
                "races": ingested,
                "expected": EXPECTED_RACES_PER_SEASON,
                "progress": min(1.0, round(ingested / EXPECTED_RACES_PER_SEASON, 3)),
                "complete": ingested >= EXPECTED_RACES_PER_SEASON - 1,
            }
        )

    embedding_sources: list[dict] = []
    try:
        rows = db.execute(
            text(
                "SELECT metadata->>'source' AS source, COUNT(*) AS n "
                "FROM race_embeddings WHERE metadata IS NOT NULL "
                "GROUP BY metadata->>'source' "
                "ORDER BY n DESC"
            )
        ).all()
        embedding_sources = [
            {"source": r.source or "unknown", "count": r.n} for r in rows
        ]
    except Exception:
        embedding_sources = []

    races_with_telemetry = _safe_scalar(
        db,
        select(func.count(func.distinct(TelemetryPath.race_id))),
    )
    races_with_embeddings = _safe_scalar(
        db,
        select(func.count(func.distinct(RaceEmbedding.race_id))).where(
            RaceEmbedding.race_id.is_not(None)
        ),
    )

    total_expected = EXPECTED_RACES_PER_SEASON * len(YEARS_TARGET)

    return {
        "headline": {
            "grand_prix": races,
            "laps_recorded": lap_times,
            "pit_stops": pit_stops,
            "telemetry_points": telemetry_points,
            "total_data_points": total_data_points,
        },
        "drivers": drivers,
        "constructors": constructors,
        "circuits": circuits,
        "safety_cars": safety_cars,
        "race_results": race_results,
        "embeddings": embeddings,
        "scenarios": scenarios,
        "telemetry_rows": telemetry_rows,
        "races_with_telemetry": races_with_telemetry,
        "races_with_embeddings": races_with_embeddings,
        "season_breakdown": season_breakdown,
        "embedding_sources": embedding_sources,
        "years_target": YEARS_TARGET,
        "total_expected_races": total_expected,
        "overall_progress": round(races / total_expected, 3) if total_expected else 0,
    }
