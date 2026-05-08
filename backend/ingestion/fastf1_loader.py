from pathlib import Path

import fastf1

from utils.normalize import normalize_points


CACHE_DIR = Path(__file__).resolve().parents[2] / "fastf1_cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))


def load_driver_lap_path(year: int, race_name: str, driver_code: str, lap_index: int = 0) -> list[dict]:
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

