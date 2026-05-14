import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fastf1
from sqlalchemy.orm import Session

from db.connection import SessionLocal
from db.models import Driver, Race, TelemetryPath

CACHE_DIR = Path(__file__).resolve().parents[2] / "fastf1_cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))


def normalize_xy(points: list[dict]) -> list[dict]:
    if not points:
        return []
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = x_max - x_min or 1
    y_span = y_max - y_min or 1
    return [
        {
            **p,
            "x": (p["x"] - x_min) / x_span,
            "y": (p["y"] - y_min) / y_span,
        }
        for p in points
    ]


def ingest_telemetry(db: Session, year: int, round_number: int) -> None:
    race = db.query(Race).filter_by(season_year=year, round=round_number).one_or_none()
    if race is None:
        print(f"Race not found: {year} round {round_number}")
        return

    print(f"Loading FastF1 session for {race.name}...")
    session = fastf1.get_session(year, race.name, "R")
    session.load(telemetry=True, laps=True, weather=False, messages=False)

    driver_cache = {d.driver_ref: d for d in db.query(Driver).all()}

    ff1_num_to_code = {}
    for drv in session.drivers:
        info = session.get_driver(drv)
        ff1_num_to_code[drv] = info["Abbreviation"]

    existing = {
        (tp.driver_id, tp.lap)
        for tp in db.query(TelemetryPath.driver_id, TelemetryPath.lap)
        .filter_by(race_id=race.id)
        .all()
    }

    total_laps = race.total_laps or 57
    inserted = 0
    skipped = 0

    for ff1_num in session.drivers:
        code = ff1_num_to_code.get(ff1_num, "").upper()
        driver = next(
            (d for d in driver_cache.values() if d.code and d.code.upper() == code),
            None,
        )
        if driver is None:
            print(f"  Driver not found in DB: {code}")
            continue

        try:
            driver_laps = session.laps.pick_drivers(ff1_num)
        except Exception as e:
            print(f"  Could not get laps for {code}: {e}")
            continue

        print(f"  Processing {code} - {len(driver_laps)} laps")

        for _, lap_row in driver_laps.iterrows():
            try:
                lap_num = int(lap_row["LapNumber"])
            except Exception:
                continue

            if lap_num < 1 or lap_num > total_laps:
                continue

            if (driver.id, lap_num) in existing:
                skipped += 1
                continue

            try:
                tel = lap_row.get_telemetry()
                if tel is None or len(tel) < 10:
                    continue

                points = []
                for _, row in tel.iterrows():
                    x = row.get("X")
                    y = row.get("Y")
                    speed = row.get("Speed")
                    t = row.get("Time")
                    if x is None or y is None:
                        continue
                    try:
                        fx, fy = float(x), float(y)
                        if math.isnan(fx) or math.isnan(fy):
                            continue
                    except (TypeError, ValueError):
                        continue

                    t_ms = 0
                    if hasattr(t, "total_seconds"):
                        t_ms = int(t.total_seconds() * 1000)

                    points.append({
                        "x": fx,
                        "y": fy,
                        "speed": float(speed) if speed is not None else 0.0,
                        "t_ms": t_ms,
                    })

                if len(points) < 10:
                    continue

                normalized = normalize_xy(points)

                tp = TelemetryPath(
                    race_id=race.id,
                    driver_id=driver.id,
                    lap=lap_num,
                    path=normalized,
                )
                db.add(tp)
                # Commit each lap individually to avoid large batch failures
                db.commit()
                existing.add((driver.id, lap_num))
                inserted += 1
                print(f"    Lap {lap_num} committed ({len(normalized)} points)")

            except Exception as e:
                db.rollback()
                print(f"    Lap {lap_num} error: {e}")
                continue

    print(f"Done. Total inserted: {inserted}, skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--round", type=int, required=True, dest="round_number")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        ingest_telemetry(db, args.year, args.round_number)
    finally:
        db.close()


if __name__ == "__main__":
    main()
