from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Circuit, Driver, LapTime, PitStop, Race


router = APIRouter(prefix="/races", tags=["races"])


@router.get("")
def list_races(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Race, Circuit.name.label("circuit_name"))
        .outerjoin(Circuit, Race.circuit_id == Circuit.id)
        .order_by(Race.season_year.desc(), Race.round.asc())
    ).all()

    return [
        {
            "id": race.id,
            "name": race.name,
            "season": race.season_year,
            "round": race.round,
            "circuit_id": race.circuit_id,
            "circuit_name": circuit_name,
            "date": race.date.isoformat() if race.date else None,
            "total_laps": race.total_laps,
        }
        for race, circuit_name in rows
    ]


@router.get("/{race_id}/laps")
def get_laps(race_id: int, db: Session = Depends(get_db)) -> dict:
    race = db.get(Race, race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="Race not found")

    pit_rows = db.execute(
        select(PitStop.driver_id, PitStop.lap, PitStop.tire_out).where(PitStop.race_id == race_id)
    ).all()
    pit_lookup = {(driver_id, lap): tire_out for driver_id, lap, tire_out in pit_rows}

    rows = db.execute(
        select(LapTime, Driver.code, Driver.driver_ref)
        .join(Driver, LapTime.driver_id == Driver.id)
        .where(LapTime.race_id == race_id)
        .order_by(LapTime.lap.asc(), LapTime.position.asc())
    ).all()

    grouped: dict[int, list[dict]] = defaultdict(list)
    for lap_time, code, driver_ref in rows:
        tire = pit_lookup.get((lap_time.driver_id, lap_time.lap))
        grouped[lap_time.lap].append(
            {
                "driver_id": lap_time.driver_id,
                "code": code or driver_ref[:3].upper(),
                "position": lap_time.position,
                "gap_ms": lap_time.gap_to_leader_ms,
                "time_ms": lap_time.time_ms,
                "tire": tire,
                "in_pit": (lap_time.driver_id, lap_time.lap) in pit_lookup,
            }
        )

    return {
        "race_id": race.id,
        "laps": [{"lap": lap, "drivers": drivers} for lap, drivers in grouped.items()],
    }

