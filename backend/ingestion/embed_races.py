"""Build RAG embeddings from race summaries.

For every race with results we synthesize 3-4 textual chunks:
  - "Race summary" - top 5 + headline narrative
  - "Pit window analysis" - pit lap distribution by driver
  - "Safety cars + incidents"
  - "Leader changes" - who led which laps

These chunks plus any FIA decision text become the RAG context Granite uses
when explaining counterfactuals or answering free-form questions.
"""

from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy import select

from ai.rag import upsert_chunks
from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race, RaceResult, SafetyCar


def _race_summary_text(db, race: Race) -> list[dict]:
    chunks: list[dict] = []

    results = db.execute(
        select(RaceResult.final_position, RaceResult.status, RaceResult.points, Driver.code, Driver.surname)
        .join(Driver, RaceResult.driver_id == Driver.id)
        .where(RaceResult.race_id == race.id)
        .order_by(RaceResult.final_position.asc())
    ).all()

    if results:
        top10 = ", ".join(
            f"P{r.final_position} {r.code or r.surname or ''} ({r.points or 0} pts)"
            for r in results[:10]
        )
        chunks.append(
            {
                "text": f"{race.name} {race.season_year}, round {race.round}. Final classification top 10: {top10}.",
                "meta": {"title": f"{race.season_year} {race.name} - Result", "kind": "result"},
            }
        )

    pit_rows = db.execute(
        select(Driver.code, PitStop.lap, PitStop.tire_in, PitStop.tire_out, PitStop.duration_ms)
        .join(Driver, PitStop.driver_id == Driver.id)
        .where(PitStop.race_id == race.id)
        .order_by(PitStop.lap.asc())
    ).all()
    if pit_rows:
        by_driver: dict[str, list[str]] = defaultdict(list)
        for code, lap, tin, tout, dur in pit_rows:
            by_driver[code or "?"].append(f"L{lap} {tin or '?'}->{tout or '?'} ({dur or '?'}ms)")
        body = "; ".join(f"{code}: {', '.join(stops)}" for code, stops in by_driver.items())
        chunks.append(
            {
                "text": f"{race.name} {race.season_year} pit windows. {body}",
                "meta": {"title": f"{race.season_year} {race.name} - Pit", "kind": "pit"},
            }
        )

    sc_rows = db.execute(
        select(SafetyCar.type, SafetyCar.lap_start, SafetyCar.lap_end).where(
            SafetyCar.race_id == race.id
        )
    ).all()
    if sc_rows:
        body = "; ".join(f"{tp} from lap {ls} to {le}" for tp, ls, le in sc_rows)
        chunks.append(
            {
                "text": f"{race.name} {race.season_year} safety car windows: {body}",
                "meta": {"title": f"{race.season_year} {race.name} - SC", "kind": "safety_car"},
            }
        )

    lap_rows = db.execute(
        select(LapTime.lap, Driver.code)
        .join(Driver, LapTime.driver_id == Driver.id)
        .where(LapTime.race_id == race.id, LapTime.position == 1)
        .order_by(LapTime.lap.asc())
    ).all()
    if lap_rows:
        prev = None
        segments: list[str] = []
        run_start = None
        for lap, code in lap_rows:
            if code != prev:
                if prev is not None and run_start is not None:
                    segments.append(f"L{run_start}-L{lap - 1} {prev}")
                prev = code
                run_start = lap
        if prev and run_start is not None and lap_rows:
            segments.append(f"L{run_start}-L{lap_rows[-1][0]} {prev}")
        if segments:
            chunks.append(
                {
                    "text": f"{race.name} {race.season_year} race lead by lap: {', '.join(segments)}",
                    "meta": {"title": f"{race.season_year} {race.name} - Lead", "kind": "lead"},
                }
            )

    return chunks


def embed_race(race_id: int) -> int:
    with SessionLocal() as db:
        race = db.get(Race, race_id)
        if race is None:
            print(f"Race {race_id} not found", flush=True)
            return 0
        chunks = _race_summary_text(db, race)
        if not chunks:
            return 0
        return upsert_chunks(db, race_id=race_id, source="race_narrative", items=chunks)


def embed_season(year: int) -> int:
    with SessionLocal() as db:
        races = db.query(Race).filter(Race.season_year == year).order_by(Race.round.asc()).all()
    total = 0
    for race in races:
        n = embed_race(race.id)
        if n:
            print(f"  embedded {n} chunks for {year}.{race.round} ({race.name})", flush=True)
        total += n
    return total


def _main() -> None:
    parser = argparse.ArgumentParser(description="Build RAG embeddings for races.")
    parser.add_argument("--years", type=int, nargs="+", default=[2019, 2020, 2021, 2022, 2023, 2024])
    parser.add_argument("--race-id", type=int, default=None)
    args = parser.parse_args()

    if args.race_id is not None:
        n = embed_race(args.race_id)
        print(f"embedded {n} chunks", flush=True)
        return

    total = 0
    for year in args.years:
        print(f"=== embedding {year} ===", flush=True)
        total += embed_season(year)
    print(f"total chunks embedded: {total}", flush=True)


if __name__ == "__main__":
    _main()
