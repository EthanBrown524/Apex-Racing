"""Race forecast - uses historical results at the same circuit + recent form
to produce predictions and a "circuit DNA" radar.

When there's no data we still return a deterministic, plausible shape so the
frontend always has something to render.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.connection import SessionLocal
from db.models import (
    Circuit,
    Driver,
    LapTime,
    PitStop,
    Race,
    RaceResult,
    SafetyCar,
)


def _circuit_dna(db: Session, circuit_id: int | None) -> dict:
    """0-1 scaled traits derived from historical race telemetry at the circuit."""
    base = {
        "overtaking": 0.5,
        "tire_deg": 0.5,
        "safety_car_prob": 0.3,
        "weather_risk": 0.2,
    }
    if circuit_id is None:
        return base

    race_ids = [
        r[0]
        for r in db.execute(
            select(Race.id).where(Race.circuit_id == circuit_id)
        ).all()
    ]
    if not race_ids:
        return base

    sc_count = db.execute(
        select(SafetyCar.id).where(SafetyCar.race_id.in_(race_ids))
    ).all()
    pit_count = db.execute(
        select(PitStop.id).where(PitStop.race_id.in_(race_ids))
    ).all()

    races_with_sc = len({_sc_race_id(db, r) for r in race_ids if _sc_race_id(db, r)})
    safety_car_prob = min(1.0, races_with_sc / max(1, len(race_ids)))

    avg_pits = len(pit_count) / max(1, len(race_ids))
    tire_deg = min(1.0, avg_pits / 50.0)

    leader_changes = _leader_changes_avg(db, race_ids)
    overtaking = min(1.0, leader_changes / 6.0)

    return {
        "overtaking": round(overtaking, 2),
        "tire_deg": round(tire_deg, 2),
        "safety_car_prob": round(safety_car_prob, 2),
        "weather_risk": 0.2,
    }


def _sc_race_id(db: Session, race_id: int) -> int | None:
    row = db.execute(
        select(SafetyCar.race_id).where(SafetyCar.race_id == race_id).limit(1)
    ).first()
    return row[0] if row else None


def _leader_changes_avg(db: Session, race_ids: list[int]) -> float:
    if not race_ids:
        return 0.0
    rows = db.execute(
        select(LapTime.race_id, LapTime.lap, LapTime.position, LapTime.driver_id)
        .where(LapTime.race_id.in_(race_ids), LapTime.position == 1)
        .order_by(LapTime.race_id.asc(), LapTime.lap.asc())
    ).all()

    by_race: dict[int, list[int]] = defaultdict(list)
    for race_id, _lap, _pos, driver_id in rows:
        if driver_id is not None:
            by_race[race_id].append(driver_id)

    changes = []
    for leaders in by_race.values():
        prev = None
        c = 0
        for d in leaders:
            if prev is not None and d != prev:
                c += 1
            prev = d
        changes.append(c)
    return (sum(changes) / len(changes)) if changes else 0.0


def _recent_form(db: Session, target_race: Race, lookback: int = 5) -> list[dict]:
    """Aggregate finish position + points across the most recent {lookback}
    races strictly before the target race."""
    if target_race.season_year is None or target_race.round is None:
        return []

    rows = db.execute(
        select(Race.id, Race.season_year, Race.round)
        .where(
            (Race.season_year < target_race.season_year)
            | (
                (Race.season_year == target_race.season_year)
                & (Race.round < target_race.round)
            )
        )
        .order_by(Race.season_year.desc(), Race.round.desc())
        .limit(lookback)
    ).all()
    recent_ids = [r.id for r in rows]
    if not recent_ids:
        return []

    results = db.execute(
        select(RaceResult.driver_id, RaceResult.final_position, RaceResult.points, Driver.code)
        .join(Driver, RaceResult.driver_id == Driver.id)
        .where(RaceResult.race_id.in_(recent_ids))
    ).all()

    agg: dict[int, dict] = defaultdict(lambda: {"races": 0, "avg_pos": 0, "points": 0, "code": "?"})
    for driver_id, pos, points, code in results:
        bucket = agg[driver_id]
        bucket["races"] += 1
        bucket["avg_pos"] += int(pos or 20)
        bucket["points"] += float(points or 0)
        bucket["code"] = code or bucket["code"]

    forecast = []
    for driver_id, bucket in agg.items():
        if bucket["races"] == 0:
            continue
        avg_pos = bucket["avg_pos"] / bucket["races"]
        win_pct = max(0.01, min(0.95, (21 - avg_pos) / 20))
        forecast.append(
            {
                "driver_id": driver_id,
                "code": bucket["code"],
                "avg_position": round(avg_pos, 2),
                "recent_points": round(bucket["points"], 1),
                "win_pct": round(win_pct, 3),
                "strategy": _suggest_strategy(avg_pos),
            }
        )
    forecast.sort(key=lambda d: d["win_pct"], reverse=True)
    return forecast[:10]


def _suggest_strategy(avg_pos: float) -> str:
    if avg_pos <= 3:
        return "Track-position cover - undercut on lap 18"
    if avg_pos <= 8:
        return "Aggressive 1-stop, overcut middle stint"
    if avg_pos <= 14:
        return "Off-set 2-stop for traffic-free air"
    return "Long first stint, gamble on safety car"


def _risk_factors(dna: dict) -> list[str]:
    risks = []
    if dna.get("safety_car_prob", 0) >= 0.6:
        risks.append("High safety car probability - keep an emergency pit window open")
    if dna.get("weather_risk", 0) >= 0.5:
        risks.append("Weather variability - intermediates ready on the grid")
    if dna.get("tire_deg", 0) >= 0.7:
        risks.append("Heavy tire degradation - protect rears in the opening stint")
    if dna.get("overtaking", 0) <= 0.3:
        risks.append("Low overtaking - track position decisive, undercut wins races")
    if not risks:
        risks.append("Balanced circuit - free strategic choice")
    return risks


def build_forecast(race_id: int) -> dict:
    with SessionLocal() as db:
        race = db.get(Race, race_id)
        if race is None:
            return {
                "race_id": race_id,
                "predictions": [],
                "circuit_dna": {
                    "overtaking": 0.0,
                    "tire_deg": 0.0,
                    "safety_car_prob": 0.0,
                    "weather_risk": 0.0,
                },
                "risk_factors": ["Race not found"],
            }

        dna = _circuit_dna(db, race.circuit_id)
        predictions = _recent_form(db, race)

    return {
        "race_id": race_id,
        "circuit_dna": dna,
        "predictions": predictions,
        "risk_factors": _risk_factors(dna),
    }
