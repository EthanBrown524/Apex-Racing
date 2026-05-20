"""Race forecast - uses historical results at the same circuit + recent form
to produce predictions and a "circuit DNA" radar.

Falls back to a plausible default shape when there's no data so the frontend
always has something to render.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race, RaceResult, SafetyCar


DEFAULT_DNA = {
    "overtaking": 0.5,
    "tire_deg": 0.5,
    "safety_car_prob": 0.3,
    "weather_risk": 0.2,
}


def _circuit_dna(db: Session, circuit_id: int | None) -> dict:
    """0-1 scaled traits derived from historical races at the circuit.

    One round-trip per stat instead of one per race.
    """
    if circuit_id is None:
        return dict(DEFAULT_DNA)

    race_ids = [
        r[0] for r in db.execute(select(Race.id).where(Race.circuit_id == circuit_id)).all()
    ]
    if not race_ids:
        return dict(DEFAULT_DNA)

    n_races = len(race_ids)

    races_with_sc = db.scalar(
        select(func.count(func.distinct(SafetyCar.race_id))).where(
            SafetyCar.race_id.in_(race_ids)
        )
    ) or 0
    safety_car_prob = min(1.0, races_with_sc / n_races)

    pit_total = db.scalar(
        select(func.count(PitStop.id)).where(PitStop.race_id.in_(race_ids))
    ) or 0
    tire_deg = min(1.0, (pit_total / n_races) / 50.0)

    overtaking = min(1.0, _leader_changes_avg(db, race_ids) / 6.0)

    return {
        "overtaking": round(overtaking, 2),
        "tire_deg": round(tire_deg, 2),
        "safety_car_prob": round(safety_car_prob, 2),
        "weather_risk": DEFAULT_DNA["weather_risk"],
    }


def _leader_changes_avg(db: Session, race_ids: list[int]) -> float:
    """Average number of distinct-leader transitions per race.

    One SQL round-trip, grouped client-side by race_id.
    """
    if not race_ids:
        return 0.0

    rows = db.execute(
        select(LapTime.race_id, LapTime.lap, LapTime.driver_id)
        .where(LapTime.race_id.in_(race_ids), LapTime.position == 1)
        .order_by(LapTime.race_id.asc(), LapTime.lap.asc())
    ).all()

    by_race: dict[int, list[int]] = defaultdict(list)
    for race_id, _lap, driver_id in rows:
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
    """Per-driver average finish + points across the most recent {lookback}
    races strictly before the target race."""
    if target_race.season_year is None or target_race.round is None:
        return []

    recent_ids = [
        r[0]
        for r in db.execute(
            select(Race.id)
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
    ]
    if not recent_ids:
        return []

    results = db.execute(
        select(
            RaceResult.driver_id,
            RaceResult.final_position,
            RaceResult.points,
            Driver.code,
        )
        .join(Driver, RaceResult.driver_id == Driver.id)
        .where(RaceResult.race_id.in_(recent_ids))
    ).all()

    agg: dict[int, dict] = defaultdict(
        lambda: {"races": 0, "pos_sum": 0, "points": 0.0, "code": "?"}
    )
    for driver_id, pos, points, code in results:
        bucket = agg[driver_id]
        bucket["races"] += 1
        bucket["pos_sum"] += int(pos or 20)
        bucket["points"] += float(points or 0)
        bucket["code"] = code or bucket["code"]

    forecast = []
    for driver_id, bucket in agg.items():
        if bucket["races"] == 0:
            continue
        avg_pos = bucket["pos_sum"] / bucket["races"]
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
                "circuit_dna": {k: 0.0 for k in DEFAULT_DNA},
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
