"""Export the database to a JSON dump for backup / portability / sharing.

This lets you ingest once on a beefy machine and ship the result to the demo
laptop without having to re-run the FastF1 pipeline.

Run:
    python -m ingestion.export --out apex_dump.json
    python -m ingestion.export --out apex_dump.json --skip-telemetry

To restore, see import.py.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Iterable

from sqlalchemy import select

from db.connection import SessionLocal
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
    Season,
    TelemetryPath,
)


def _rows(db, model, columns: Iterable[str]) -> list[dict]:
    rows = db.execute(select(model)).scalars().all()
    return [{col: _serialize(getattr(row, col)) for col in columns} for row in rows]


def _serialize(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def export(out_path: str, skip_telemetry: bool, skip_embeddings: bool) -> None:
    t0 = time.time()
    payload: dict = {"version": 1, "exported_at": time.time()}

    with SessionLocal() as db:
        payload["seasons"] = _rows(db, Season, ["year"])
        payload["circuits"] = _rows(
            db, Circuit, ["id", "name", "location", "country", "length_km", "gps_path", "gps_image"]
        )
        payload["drivers"] = _rows(
            db, Driver, ["id", "driver_ref", "code", "forename", "surname", "nationality"]
        )
        payload["constructors"] = _rows(
            db, Constructor, ["id", "constructor_ref", "name", "nationality"]
        )
        payload["races"] = _rows(
            db, Race, ["id", "season_year", "round", "circuit_id", "name", "date", "total_laps"]
        )
        payload["race_results"] = _rows(
            db,
            RaceResult,
            ["id", "race_id", "driver_id", "constructor_id", "grid_position", "final_position", "points", "status"],
        )
        payload["lap_times"] = _rows(
            db, LapTime, ["id", "race_id", "driver_id", "lap", "position", "time_ms", "gap_to_leader_ms"]
        )
        payload["pit_stops"] = _rows(
            db, PitStop, ["id", "race_id", "driver_id", "stop_number", "lap", "duration_ms", "tire_in", "tire_out"]
        )
        payload["safety_cars"] = _rows(
            db, SafetyCar, ["id", "race_id", "type", "lap_start", "lap_end"]
        )
        payload["scenarios"] = _rows(
            db, Scenario, ["id", "label", "race_id", "changes", "created_at"]
        )

        if not skip_telemetry:
            payload["telemetry_paths"] = _rows(
                db, TelemetryPath, ["id", "race_id", "driver_id", "lap", "path"]
            )
        else:
            payload["telemetry_paths"] = []

        if not skip_embeddings:
            embeds = []
            rows = db.execute(select(RaceEmbedding)).scalars().all()
            for row in rows:
                embedding = row.embedding
                if isinstance(embedding, str):
                    try:
                        embedding = [float(x) for x in embedding.strip("[]").split(",") if x.strip()]
                    except Exception:
                        embedding = []
                embeds.append(
                    {
                        "id": row.id,
                        "race_id": row.race_id,
                        "content": row.content,
                        "embedding": list(embedding) if embedding else [],
                        "metadata": row.metadata_,
                    }
                )
            payload["race_embeddings"] = embeds
        else:
            payload["race_embeddings"] = []

    counts = {k: len(v) for k, v in payload.items() if isinstance(v, list)}

    with open(out_path, "w") as fh:
        json.dump(payload, fh, default=_serialize)

    elapsed = round(time.time() - t0, 1)
    print(f"Exported in {elapsed}s. Row counts:", file=sys.stderr)
    for table, n in counts.items():
        print(f"  {table:>20}: {n:,}", file=sys.stderr)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Dump the APEX DB to JSON.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    parser.add_argument("--skip-telemetry", action="store_true")
    parser.add_argument("--skip-embeddings", action="store_true")
    args = parser.parse_args()

    export(args.out, args.skip_telemetry, args.skip_embeddings)


if __name__ == "__main__":
    _main()
