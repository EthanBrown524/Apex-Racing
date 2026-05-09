from pathlib import Path

import fastf1
import fastf1.plotting
from sqlalchemy.orm import Session

from db.models import Circuit, Race
from utils.normalize import normalize_points

CACHE_DIR = Path(__file__).resolve().parents[2] / "fastf1_cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))


def _extract_circuit_outline(session) -> list[dict]:
    """Extract a clean circuit outline from the fastest lap of any driver."""
    fastest_lap = session.laps.pick_fastest()
    telemetry = fastest_lap.get_telemetry()

    points = [
        {
            "x": float(row.X),
            "y": float(row.Y),
            "distance_pct": float(row.Distance / telemetry["Distance"].max()),
            "speed": float(row.Speed),
        }
        for row in telemetry.itertuples()
        if row.X is not None and row.Y is not None
    ]
    return normalize_points(points)


def ingest_circuit_path(db: Session, year: int, round_number: int) -> None:
    """Load FastF1 telemetry for a race and store the circuit outline."""
    race = db.query(Race).filter_by(season_year=year, round=round_number).one_or_none()
    if race is None:
        print(f"  Race not found: {year} round {round_number}")
        return

    circuit = db.get(Circuit, race.circuit_id)
    if circuit is None:
        print(f"  Circuit not found for race id {race.id}")
        return

    print(f"  Loading FastF1 session for {race.name}...")
    session = fastf1.get_session(year, race.name, "R")
    session.load(telemetry=True, laps=True, weather=False, messages=False)

    print(f"  Extracting circuit outline...")
    path = _extract_circuit_outline(session)

    circuit.gps_path = path
    db.commit()
    print(f"  Stored {len(path)} points for {circuit.name}")


def load_driver_lap_path(
    year: int, race_name: str, driver_code: str, lap_index: int = 0
) -> list[dict]:
    """Load telemetry for a specific driver lap (used for telemetry_paths table later)."""
    session = fastf1.get_session(year, race_name, "R")
    session.load()
    lap = session.laps.pick_driver(driver_code).iloc[lap_index]
    telemetry = lap.get_telemetry()

    points = [
        {
            "x": float(row.X),
            "y": float(row.Y),
            "distance_pct": float(row.Distance / telemetry["Distance"].max()),
            "speed": float(row.Speed),
        }
        for row in telemetry.itertuples()
    ]
    return normalize_points(points)