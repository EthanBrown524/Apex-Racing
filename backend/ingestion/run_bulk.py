"""Bulk ingestion for the 2019-2024 seasons.

This script orchestrates four phases per season:
  1. ergast metadata + results + lap times + pit stops
  2. fastf1 circuit GPS path (one round per circuit, idempotent)
  3. telemetry paths for a sample of laps (configurable)
  4. embeddings index built from race summaries

Run:
    python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024
    python -m ingestion.run_bulk --years 2023 --skip-telemetry --skip-embeddings

The script is restart-safe: each phase no-ops if the corresponding rows already
exist (results count > 0, gps_path not null, telemetry rows present, etc).
"""

from __future__ import annotations

import argparse
import time
from typing import Iterable

from db.connection import SessionLocal
from db.models import Race
from ingestion.ergast import ingest_season


YEARS_DEFAULT = [2019, 2020, 2021, 2022, 2023, 2024]


def _ingest_circuit_paths_for_year(year: int) -> None:
    """For each circuit referenced in {year}, pull a fastf1 circuit outline if
    we don't have one yet. Failures are isolated per-circuit so one stale
    cache entry doesn't kill the whole run."""
    try:
        from ingestion.fastf1_loader import ingest_circuit_path
    except Exception as exc:
        print(f"  fastf1 unavailable ({exc}); skipping circuit paths", flush=True)
        return

    with SessionLocal() as db:
        races = (
            db.query(Race)
            .filter(Race.season_year == year)
            .order_by(Race.round.asc())
            .all()
        )
        seen_circuits: set[int] = set()
        for race in races:
            if race.circuit_id in seen_circuits or race.circuit_id is None:
                continue
            seen_circuits.add(race.circuit_id)
            try:
                ingest_circuit_path(db, year=year, round_number=race.round)
                db.commit()
                print(f"  circuit path {year}.{race.round} ({race.name})", flush=True)
            except Exception as exc:
                db.rollback()
                print(f"  skip {year}.{race.round} circuit: {exc}", flush=True)


def _ingest_telemetry_for_year(year: int, sample_laps: int = 10) -> None:
    """Telemetry is the bulkiest data; we sample `sample_laps` evenly-spaced
    laps per race rather than every lap."""
    try:
        from ingestion.run_telemetry import ingest_telemetry
    except Exception as exc:
        print(f"  telemetry import failed ({exc}); skipping", flush=True)
        return

    with SessionLocal() as db:
        races = db.query(Race).filter(Race.season_year == year).order_by(Race.round.asc()).all()

    for race in races:
        total = race.total_laps or 0
        if total <= 0:
            continue
        step = max(1, total // sample_laps)
        laps = list(range(1, total + 1, step))[:sample_laps]
        try:
            ingest_telemetry(year=year, round_number=race.round, laps=laps)
            print(f"  telemetry {year}.{race.round} laps={laps}", flush=True)
        except TypeError:
            try:
                ingest_telemetry(year=year, round_number=race.round)
                print(f"  telemetry {year}.{race.round} (full)", flush=True)
            except Exception as exc:
                print(f"  skip telemetry {year}.{race.round}: {exc}", flush=True)
        except Exception as exc:
            print(f"  skip telemetry {year}.{race.round}: {exc}", flush=True)


def _ingest_embeddings_for_year(year: int) -> None:
    try:
        from ingestion.embed_races import embed_season
    except Exception as exc:
        print(f"  embeddings import failed ({exc}); skipping", flush=True)
        return
    embed_season(year)


def run(years: Iterable[int], skip_telemetry: bool, skip_embeddings: bool, skip_circuits: bool) -> None:
    for year in years:
        t0 = time.time()
        print(f"\n=== INGESTING {year} ===", flush=True)
        with SessionLocal() as db:
            try:
                ingest_season(db, year=year)
            except Exception as exc:
                print(f"  ergast phase failed: {exc}", flush=True)

        if not skip_circuits:
            _ingest_circuit_paths_for_year(year)
        if not skip_telemetry:
            _ingest_telemetry_for_year(year)
        if not skip_embeddings:
            _ingest_embeddings_for_year(year)
        print(f"=== {year} done in {time.time() - t0:.1f}s ===", flush=True)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Bulk-ingest F1 seasons.")
    parser.add_argument("--years", type=int, nargs="+", default=YEARS_DEFAULT)
    parser.add_argument("--skip-telemetry", action="store_true")
    parser.add_argument("--skip-embeddings", action="store_true")
    parser.add_argument("--skip-circuits", action="store_true")
    args = parser.parse_args()

    run(
        years=args.years,
        skip_telemetry=args.skip_telemetry,
        skip_embeddings=args.skip_embeddings,
        skip_circuits=args.skip_circuits,
    )


if __name__ == "__main__":
    _main()
