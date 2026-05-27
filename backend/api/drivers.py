"""Driver-centric endpoints.

`GET /drivers/{code}/season-points/{year}` returns a per-round breakdown of
the driver's points plus a running cumulative total for the given season.
Used by the Driver page (`/driver/:code/:year`) and Standings page to plot
cumulative point lines without re-deriving the math client-side.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Driver, Race, RaceResult


router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/{code}/season-points/{year}")
def season_points(
    code: str, year: int, db: Session = Depends(get_db)
) -> dict:
    code = code.upper().strip()
    driver = db.execute(
        select(Driver).where(Driver.code == code)
    ).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=404, detail=f"Driver {code} not found")

    rows = db.execute(
        select(
            Race.round,
            Race.name,
            Race.date,
            RaceResult.points,
            RaceResult.final_position,
            RaceResult.grid_position,
        )
        .join(RaceResult, RaceResult.race_id == Race.id)
        .where(
            RaceResult.driver_id == driver.id,
            Race.season_year == year,
        )
        .order_by(Race.round.asc())
    ).all()

    if not rows:
        return {
            "driver_code": code,
            "driver_name": f"{driver.forename or ''} {driver.surname or ''}".strip(),
            "year": year,
            "races": [],
            "total_points": 0.0,
        }

    cumulative = 0.0
    races: list[dict] = []
    for row in rows:
        pts = float(row.points or 0.0)
        cumulative += pts
        races.append(
            {
                "round": row.round,
                "race_name": row.name,
                "date": row.date.isoformat() if row.date else None,
                "points": round(pts, 1),
                "cumulative_points": round(cumulative, 1),
                "final_position": row.final_position,
                "grid_position": row.grid_position,
            }
        )

    return {
        "driver_code": code,
        "driver_name": f"{driver.forename or ''} {driver.surname or ''}".strip(),
        "year": year,
        "races": races,
        "total_points": round(cumulative, 1),
    }


@router.get("/{code}")
def driver_summary(code: str, db: Session = Depends(get_db)) -> dict:
    """Lightweight metadata endpoint - used as a header on the Driver page."""
    code = code.upper().strip()
    driver = db.execute(
        select(Driver).where(Driver.code == code)
    ).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=404, detail=f"Driver {code} not found")

    return {
        "code": driver.code,
        "driver_ref": driver.driver_ref,
        "forename": driver.forename,
        "surname": driver.surname,
        "nationality": driver.nationality,
    }
