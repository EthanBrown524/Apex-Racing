"""Print the current ingestion status per season.

Useful for "did my overnight job finish?" and for screenshots in the demo.

Run:
    python -m ingestion.status
"""

from __future__ import annotations

import argparse

from sqlalchemy import func, select

from db.connection import SessionLocal
from db.models import LapTime, PitStop, Race, RaceEmbedding, TelemetryPath


YEARS_DEFAULT = [2019, 2020, 2021, 2022, 2023, 2024]


def _bar(progress: float, width: int = 24) -> str:
    filled = int(round(progress * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def status(years: list[int]) -> None:
    with SessionLocal() as db:
        for year in years:
            race_ids = [
                r[0] for r in db.execute(select(Race.id).where(Race.season_year == year)).all()
            ]
            n_races = len(race_ids)
            if not race_ids:
                print(f"  {year}  {_bar(0)}  0 races (not ingested)")
                continue

            laps = db.scalar(
                select(func.count(LapTime.id)).where(LapTime.race_id.in_(race_ids))
            ) or 0
            pits = db.scalar(
                select(func.count(PitStop.id)).where(PitStop.race_id.in_(race_ids))
            ) or 0
            telem = db.scalar(
                select(func.count(TelemetryPath.id)).where(
                    TelemetryPath.race_id.in_(race_ids)
                )
            ) or 0
            embeds = db.scalar(
                select(func.count(RaceEmbedding.id)).where(
                    RaceEmbedding.race_id.in_(race_ids)
                )
            ) or 0
            progress = min(1.0, n_races / 22)
            print(
                f"  {year}  {_bar(progress)}  {n_races:>2} races | "
                f"{laps:>6,} laps | {pits:>4,} pits | "
                f"{telem:>6,} telemetry | {embeds:>4,} embeds"
            )


def _main() -> None:
    parser = argparse.ArgumentParser(description="Print ingestion status per season.")
    parser.add_argument("--years", type=int, nargs="+", default=YEARS_DEFAULT)
    args = parser.parse_args()

    print("\nAPEX ingestion status")
    print("=" * 90)
    status(args.years)
    print()


if __name__ == "__main__":
    _main()
