"""Backfill pit_stops.tire_in / tire_out and safety_cars from FastF1.

FastF1's session.laps DataFrame carries per-lap Compound, Stint, and
PitInTime/PitOutTime columns. We derive tire_in / tire_out as the compound
of the stint ending and the compound of the stint starting at each pit
lap.

Track-status info (SC1/SC2/VSC) lives in session.track_status — a tick
stream of status flags. We collapse consecutive ticks into windows and
write one row per window to safety_cars.

Run:
    python -m ingestion.run_tires --years 2019 2020 2021 2022 2023 2024
    python -m ingestion.run_tires --years 2023 --rounds 7 8
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import fastf1
from sqlalchemy import select
from sqlalchemy.orm import Session
from tqdm import tqdm

from db.connection import SessionLocal
from db.models import Driver, PitStop, Race, SafetyCar

warnings.filterwarnings("ignore")
CACHE_DIR = Path(__file__).resolve().parents[2] / "fastf1_cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))


# FastF1 TrackStatus codes (single char):
#   '1' = AllClear, '2' = Yellow, '4' = SafetyCar, '5' = RedFlag,
#   '6' = VirtualSafetyCar, '7' = VirtualSafetyCarEnding
SC_CODES = {"4": "SC", "6": "VSC"}


def _normalize_driver_code(raw: str) -> str:
    return (raw or "").strip().upper()[:3]


def _laps_to_stints(laps_df) -> dict[str, list[dict]]:
    """Return {driver_code: [{stint, compound, first_lap, last_lap, pit_in_lap}]}"""
    out: dict[str, list[dict]] = {}
    if laps_df is None or laps_df.empty:
        return out

    for driver_code, group in laps_df.groupby("Driver"):
        code = _normalize_driver_code(str(driver_code))
        if not code:
            continue
        stints: list[dict] = []
        for stint_num, sg in group.groupby("Stint"):
            if sg.empty:
                continue
            compound = sg["Compound"].dropna()
            if compound.empty:
                continue
            pit_rows = sg[sg["PitInTime"].notna()]
            pit_in_lap = (
                int(pit_rows["LapNumber"].iloc[0]) if not pit_rows.empty else None
            )
            stints.append(
                {
                    "stint": int(stint_num) if stint_num is not None else 0,
                    "compound": str(compound.iloc[0]),
                    "first_lap": int(sg["LapNumber"].min()),
                    "last_lap": int(sg["LapNumber"].max()),
                    "pit_in_lap": pit_in_lap,
                }
            )
        stints.sort(key=lambda s: s["stint"])
        out[code] = stints
    return out


def _driver_id_by_code(db: Session) -> dict[str, int]:
    rows = db.execute(select(Driver.id, Driver.code)).all()
    return {r.code: r.id for r in rows if r.code}


def _backfill_tires_for_race(db: Session, race: Race) -> int:
    """Returns count of pit_stops rows updated."""
    session = fastf1.get_session(race.season_year, race.name, "R")
    session.load(telemetry=False, laps=True, weather=False, messages=False)

    stints_by_driver = _laps_to_stints(session.laps)
    if not stints_by_driver:
        return 0

    drivers = _driver_id_by_code(db)
    pit_stops = db.execute(
        select(PitStop).where(PitStop.race_id == race.id)
    ).scalars().all()

    by_driver_lap: dict[tuple[int, int], PitStop] = {
        (p.driver_id, p.lap): p for p in pit_stops if p.driver_id and p.lap
    }

    updated = 0
    for code, stints in stints_by_driver.items():
        driver_id = drivers.get(code)
        if driver_id is None:
            continue
        for i, stint in enumerate(stints):
            pit_lap = stint.get("pit_in_lap")
            if pit_lap is None:
                continue
            tire_in = stint["compound"][:10] if stint["compound"] else None
            tire_out = None
            if i + 1 < len(stints):
                next_compound = stints[i + 1]["compound"]
                tire_out = next_compound[:10] if next_compound else None
            row = by_driver_lap.get((driver_id, pit_lap))
            if row is None:
                # try lap +/- 1 for off-by-one between FastF1 and Ergast
                for off in (-1, 1, -2, 2):
                    row = by_driver_lap.get((driver_id, pit_lap + off))
                    if row is not None:
                        break
            if row is None:
                continue
            if tire_in:
                row.tire_in = tire_in
            if tire_out:
                row.tire_out = tire_out
            updated += 1
    return updated


def _backfill_safety_cars_for_race(db: Session, race: Race) -> int:
    """Returns count of safety_cars rows inserted (skips if any already exist)."""
    existing = db.execute(
        select(SafetyCar).where(SafetyCar.race_id == race.id)
    ).scalars().all()
    if existing:
        return 0

    session = fastf1.get_session(race.season_year, race.name, "R")
    # Load laps AND messages together so we can map track-status timestamps
    # back to lap numbers.
    session.load(telemetry=False, laps=True, weather=False, messages=True)

    track_status = getattr(session, "track_status", None)
    if track_status is None or track_status.empty:
        return 0

    laps_df = session.laps if hasattr(session, "laps") else None

    def _lap_at(time) -> int | None:
        if laps_df is None or laps_df.empty or time is None:
            return None
        try:
            snap = laps_df[laps_df["LapStartTime"] <= time]
        except Exception:
            return None
        if snap.empty:
            return None
        try:
            return int(snap["LapNumber"].max())
        except Exception:
            return None

    inserted = 0
    open_window: dict | None = None
    for row in track_status.itertuples():
        status = str(getattr(row, "Status", "") or "")
        time = getattr(row, "Time", None)
        if status in SC_CODES and open_window is None:
            open_window = {
                "type": SC_CODES[status],
                "lap_start": _lap_at(time) or 1,
                "time_start": time,
            }
        elif open_window is not None and status not in SC_CODES:
            lap_end = _lap_at(time) or open_window["lap_start"]
            db.add(
                SafetyCar(
                    race_id=race.id,
                    type=open_window["type"],
                    lap_start=open_window["lap_start"],
                    lap_end=lap_end,
                )
            )
            inserted += 1
            open_window = None
    return inserted


def backfill_race(year: int, round_number: int) -> dict:
    with SessionLocal() as db:
        race = db.execute(
            select(Race).where(Race.season_year == year, Race.round == round_number)
        ).scalar_one_or_none()
        if race is None:
            return {"ok": False, "year": year, "round": round_number, "error": "race-missing"}

        result = {"ok": True, "year": year, "round": round_number, "race": race.name}
        try:
            result["tires_updated"] = _backfill_tires_for_race(db, race)
        except Exception as exc:
            result["tires_updated"] = 0
            result["tire_error"] = str(exc)[:160]
        try:
            result["safety_cars_added"] = _backfill_safety_cars_for_race(db, race)
        except Exception as exc:
            result["safety_cars_added"] = 0
            result["safety_car_error"] = str(exc)[:160]
        db.commit()
        return result


def _main() -> None:
    parser = argparse.ArgumentParser(description="Backfill tire compounds and safety car windows.")
    parser.add_argument("--years", type=int, nargs="*", default=[2019, 2020, 2021, 2022, 2023, 2024])
    parser.add_argument("--rounds", type=int, nargs="*", default=None)
    args = parser.parse_args()

    with SessionLocal() as db:
        q = select(Race.season_year, Race.round).where(Race.season_year.in_(args.years))
        if args.rounds:
            q = q.where(Race.round.in_(args.rounds))
        targets = sorted(db.execute(q.order_by(Race.season_year, Race.round)).all())

    total_tires = 0
    total_sc = 0
    failed = 0
    for year, rnd in tqdm(targets, desc="Backfilling tires + SC"):
        out = backfill_race(year, rnd)
        if out.get("ok"):
            total_tires += out.get("tires_updated", 0)
            total_sc += out.get("safety_cars_added", 0)
            if out.get("tire_error") or out.get("safety_car_error"):
                tqdm.write(f"  {year} r{rnd}: partial - {out}")
        else:
            failed += 1
            tqdm.write(f"  {year} r{rnd}: FAIL {out}")

    print(f"\nDone. tires_updated={total_tires}  safety_cars_inserted={total_sc}  failed={failed}")


if __name__ == "__main__":
    _main()
