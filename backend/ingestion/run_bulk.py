"""Bulk ingestion for the 2019-2024 seasons.

Per-year phases:
  1. ergast metadata + results + lap times + pit stops
  2. fastf1 circuit GPS paths (one path per circuit, idempotent)
  3. telemetry paths (sampled laps unless --full-telemetry)
  4. embeddings index built from race summaries

Run:
    python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024
    python -m ingestion.run_bulk --years 2023 --skip-telemetry --skip-embeddings
    python -m ingestion.run_bulk --years 2019 2020 --parallel-years 2

Restart-safe: each phase no-ops if the rows already exist.
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Iterable

from sqlalchemy import func, select

from db.connection import SessionLocal
from db.models import LapTime, PitStop, Race, RaceEmbedding, RaceResult, TelemetryPath
from ingestion.ergast import ingest_season


YEARS_DEFAULT = [2019, 2020, 2021, 2022, 2023, 2024]


def _try_tqdm(iterable, total=None, desc=""):
    try:
        from tqdm import tqdm

        return tqdm(iterable, total=total, desc=desc, unit="race", leave=False)
    except Exception:
        return iterable


def _year_baseline(year: int) -> dict:
    with SessionLocal() as db:
        race_ids = [
            r[0] for r in db.execute(select(Race.id).where(Race.season_year == year)).all()
        ]
        if not race_ids:
            return {"races": 0, "lap_times": 0, "pit_stops": 0, "telemetry": 0, "embeddings": 0}
        return {
            "races": len(race_ids),
            "lap_times": db.scalar(
                select(func.count(LapTime.id)).where(LapTime.race_id.in_(race_ids))
            )
            or 0,
            "pit_stops": db.scalar(
                select(func.count(PitStop.id)).where(PitStop.race_id.in_(race_ids))
            )
            or 0,
            "telemetry": db.scalar(
                select(func.count(TelemetryPath.id)).where(
                    TelemetryPath.race_id.in_(race_ids)
                )
            )
            or 0,
            "embeddings": db.scalar(
                select(func.count(RaceEmbedding.id)).where(
                    RaceEmbedding.race_id.in_(race_ids)
                )
            )
            or 0,
        }


def _ingest_circuit_paths_for_year(year: int) -> int:
    try:
        from ingestion.fastf1_loader import ingest_circuit_path
    except Exception as exc:
        print(f"  fastf1 unavailable ({exc}); skipping circuit paths", flush=True)
        return 0

    written = 0
    with SessionLocal() as db:
        races = (
            db.query(Race)
            .filter(Race.season_year == year)
            .order_by(Race.round.asc())
            .all()
        )
        seen_circuits: set[int] = set()
        for race in _try_tqdm(races, total=len(races), desc=f"{year} circuits"):
            if race.circuit_id in seen_circuits or race.circuit_id is None:
                continue
            seen_circuits.add(race.circuit_id)
            try:
                ingest_circuit_path(db, year=year, round_number=race.round)
                db.commit()
                written += 1
            except Exception as exc:
                db.rollback()
                print(f"  skip {year}.{race.round} circuit: {exc}", flush=True)
    return written


def _ingest_telemetry_for_year(year: int, sample_laps: int = 10, full: bool = False) -> int:
    try:
        from ingestion.run_telemetry import ingest_telemetry
    except Exception as exc:
        print(f"  telemetry import failed ({exc}); skipping", flush=True)
        return 0

    written = 0
    with SessionLocal() as db:
        races = (
            db.query(Race).filter(Race.season_year == year).order_by(Race.round.asc()).all()
        )

    for race in _try_tqdm(races, total=len(races), desc=f"{year} telemetry"):
        total = race.total_laps or 0
        if total <= 0:
            continue
        try:
            if full:
                ingest_telemetry(year=year, round_number=race.round)
            else:
                step = max(1, total // sample_laps)
                laps = list(range(1, total + 1, step))[:sample_laps]
                try:
                    ingest_telemetry(year=year, round_number=race.round, laps=laps)
                except TypeError:
                    ingest_telemetry(year=year, round_number=race.round)
            written += 1
        except Exception as exc:
            print(f"  skip telemetry {year}.{race.round}: {exc}", flush=True)
    return written


def _ingest_embeddings_for_year(year: int) -> int:
    try:
        from ingestion.embed_races import embed_season
    except Exception as exc:
        print(f"  embeddings import failed ({exc}); skipping", flush=True)
        return 0
    return embed_season(year)


def _process_year(args: tuple[int, bool, bool, bool, bool]) -> dict:
    year, skip_circuits, skip_telemetry, skip_embeddings, full_telemetry = args
    t0 = time.time()
    summary: dict[str, object] = {"year": year, "ok": True}

    try:
        with SessionLocal() as db:
            ingest_season(db, year=year)
    except Exception as exc:
        summary["ergast_error"] = str(exc)
        summary["ok"] = False
        return summary

    if not skip_circuits:
        try:
            summary["circuits"] = _ingest_circuit_paths_for_year(year)
        except Exception as exc:
            summary["circuits_error"] = str(exc)
    if not skip_telemetry:
        try:
            summary["telemetry_races"] = _ingest_telemetry_for_year(
                year, full=full_telemetry
            )
        except Exception as exc:
            summary["telemetry_error"] = str(exc)
    if not skip_embeddings:
        try:
            summary["embeddings"] = _ingest_embeddings_for_year(year)
        except Exception as exc:
            summary["embeddings_error"] = str(exc)

    baseline = _year_baseline(year)
    summary.update(baseline)
    summary["elapsed_seconds"] = round(time.time() - t0, 1)
    return summary


def run(
    years: Iterable[int],
    skip_telemetry: bool,
    skip_embeddings: bool,
    skip_circuits: bool,
    full_telemetry: bool,
    parallel_years: int,
) -> list[dict]:
    years = list(years)
    print(
        f"\n=== APEX BULK INGEST: {len(years)} seasons "
        f"({'parallel x' + str(parallel_years) if parallel_years > 1 else 'serial'}) ===\n",
        flush=True,
    )
    args = [
        (year, skip_circuits, skip_telemetry, skip_embeddings, full_telemetry)
        for year in years
    ]
    results: list[dict] = []

    if parallel_years > 1:
        with ProcessPoolExecutor(max_workers=parallel_years) as ex:
            futures = {ex.submit(_process_year, a): a[0] for a in args}
            for fut in as_completed(futures):
                year = futures[fut]
                try:
                    result = fut.result()
                except Exception as exc:
                    result = {"year": year, "ok": False, "error": str(exc)}
                results.append(result)
                _print_year_summary(result)
    else:
        for a in args:
            result = _process_year(a)
            results.append(result)
            _print_year_summary(result)

    _print_grand_total(results)
    return results


def _print_year_summary(summary: dict) -> None:
    year = summary["year"]
    ok = "OK " if summary.get("ok", True) else "FAIL"
    print(
        f"  [{ok}] {year}: races={summary.get('races', 0)}, "
        f"laps={summary.get('lap_times', 0)}, "
        f"pits={summary.get('pit_stops', 0)}, "
        f"telemetry={summary.get('telemetry', 0)}, "
        f"embeds={summary.get('embeddings', 0)}, "
        f"in {summary.get('elapsed_seconds', 0)}s",
        flush=True,
    )


def _print_grand_total(results: list[dict]) -> None:
    total_races = sum(r.get("races", 0) for r in results)
    total_laps = sum(r.get("lap_times", 0) for r in results)
    total_pits = sum(r.get("pit_stops", 0) for r in results)
    total_telem = sum(r.get("telemetry", 0) for r in results)
    total_embeds = sum(r.get("embeddings", 0) for r in results)
    elapsed = sum(r.get("elapsed_seconds", 0) for r in results)
    print("\n=== TOTALS ===", flush=True)
    print(f"  Races:        {total_races:>8,}", flush=True)
    print(f"  Lap times:    {total_laps:>8,}", flush=True)
    print(f"  Pit stops:    {total_pits:>8,}", flush=True)
    print(f"  Telemetry:    {total_telem:>8,}", flush=True)
    print(f"  Embeddings:   {total_embeds:>8,}", flush=True)
    print(f"  Total time:   {elapsed:>8.1f}s\n", flush=True)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Bulk-ingest F1 seasons.")
    parser.add_argument("--years", type=int, nargs="+", default=YEARS_DEFAULT)
    parser.add_argument("--skip-telemetry", action="store_true")
    parser.add_argument("--skip-embeddings", action="store_true")
    parser.add_argument("--skip-circuits", action="store_true")
    parser.add_argument(
        "--full-telemetry",
        action="store_true",
        help="Ingest every lap of telemetry (slow). Default samples ~10 laps/race.",
    )
    parser.add_argument(
        "--parallel-years",
        type=int,
        default=1,
        help="Process N years in parallel using multiprocessing (default 1 = serial).",
    )
    args = parser.parse_args()

    if args.parallel_years < 1:
        print("--parallel-years must be >= 1", file=sys.stderr)
        sys.exit(2)

    run(
        years=args.years,
        skip_telemetry=args.skip_telemetry,
        skip_embeddings=args.skip_embeddings,
        skip_circuits=args.skip_circuits,
        full_telemetry=args.full_telemetry,
        parallel_years=args.parallel_years,
    )


if __name__ == "__main__":
    _main()
