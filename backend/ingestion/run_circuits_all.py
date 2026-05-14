"""
Ingest circuit GPS paths for all rounds of all seasons with GPS data.
Renders each circuit to a PNG image and stores it as base64 in the DB.
Skips circuits that already have both gps_path and gps_image.
"""
import base64
import io
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fastf1
import fastf1.plotting
from PIL import Image, ImageDraw

from db.connection import SessionLocal
from db.models import Circuit, Race
from sqlalchemy.orm import Session

CACHE_DIR = Path(__file__).resolve().parents[2] / "fastf1_cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))

# Only years with confirmed GPS data
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

# Image render settings
IMG_WIDTH = 800
IMG_HEIGHT = 500
PADDING = 60


def normalize_points(points: list[dict]) -> list[dict]:
    if not points:
        return []
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    x_span = max(xs) - min(xs) or 1
    y_span = max(ys) - min(ys) or 1
    return [
        {**p, "x": (p["x"] - min(xs)) / x_span, "y": (p["y"] - min(ys)) / y_span}
        for p in points
    ]


def render_circuit_image(path: list[dict], color: str = "#e8002d") -> str:
    """Render circuit path to PNG and return as base64 data URL."""
    img = Image.new("RGBA", (IMG_WIDTH, IMG_HEIGHT), (13, 14, 17, 255))
    draw = ImageDraw.Draw(img)

    def to_px(point):
        x = int(point["x"] * (IMG_WIDTH - PADDING * 2) + PADDING)
        y = int(point["y"] * (IMG_HEIGHT - PADDING * 2) + PADDING)
        return (x, y)

    points_px = [to_px(p) for p in path]

    # Base track (dark)
    draw.line(points_px + [points_px[0]], fill=(30, 32, 40), width=22)

    # Speed colored overlay
    for i in range(len(path) - 1):
        speed = path[i].get("speed", 200)
        t = min(max((speed - 60) / (330 - 60), 0), 1)
        r = int(t * 220)
        g = int((1 - abs(t - 0.5) * 2) * 160)
        b = int((1 - t) * 220)
        draw.line([points_px[i], points_px[i + 1]], fill=(r, g, b), width=10)

    # Center line
    for i in range(0, len(points_px) - 1, 2):
        draw.line([points_px[i], points_px[i + 1]],
                  fill=(255, 255, 255, 18), width=2)

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def ingest_circuit_for_round(
    db: Session, year: int, round_number: int, force: bool = False
) -> bool:
    race = db.query(Race).filter_by(season_year=year, round=round_number).one_or_none()
    if race is None:
        print(f"    Race not in DB: {year} round {round_number}")
        return False

    circuit = db.get(Circuit, race.circuit_id)
    if circuit is None:
        print(f"    Circuit not found for race {race.name}")
        return False

    if not force and circuit.gps_path and circuit.gps_image:
        print(f"    Already ingested: {circuit.name}")
        return True

    print(f"    Loading FastF1 for {race.name} ({year})...")
    try:
        session = fastf1.get_session(year, race.name, "R")
        session.load(telemetry=True, laps=True, weather=False, messages=False)
        fastest = session.laps.pick_fastest()
        tel = fastest.get_telemetry()

        points = []
        for _, row in tel.iterrows():
            x, y = row.get("X"), row.get("Y")
            speed = row.get("Speed", 200)
            if x is None or y is None:
                continue
            try:
                fx, fy = float(x), float(y)
                if math.isnan(fx) or math.isnan(fy):
                    continue
            except (TypeError, ValueError):
                continue
            points.append({"x": fx, "y": fy, "speed": float(speed)})

        if len(points) < 50:
            print(f"    Not enough points for {circuit.name}")
            return False

        normalized = normalize_points(points)
        circuit.gps_path = normalized
        circuit.gps_image = render_circuit_image(normalized)
        db.commit()
        print(f"    OK {circuit.name} - {len(normalized)} points, image rendered")
        return True

    except Exception as e:
        db.rollback()
        print(f"    ERROR: {e}")
        return False


def main():
    db = SessionLocal()
    try:
        for year in YEARS:
            print(f"\n=== {year} ===")
            try:
                schedule = fastf1.get_event_schedule(year, include_testing=False)
                rounds = schedule[schedule["EventFormat"] != "testing"]["RoundNumber"].tolist()
            except Exception as e:
                print(f"  Could not get schedule: {e}")
                continue

            for round_number in rounds:
                print(f"  Round {round_number}")
                ingest_circuit_for_round(db, year, round_number)

    finally:
        db.close()


if __name__ == "__main__":
    main()
