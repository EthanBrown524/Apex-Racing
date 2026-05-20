"""Championship Impact - the signature "wow" feature.

Given a counterfactual at race X, recompute the end-of-season driver and
constructor standings assuming every other race is unchanged. Reports the
delta and whether the championship leader would have changed.

Points system: F1 awards 25 / 18 / 15 / 12 / 10 / 8 / 6 / 4 / 2 / 1 for
positions 1 through 10. Fastest-lap bonus is ignored (no reliable historical
flag in the schema).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.counterfactual import simulate_counterfactual
from ai.granite import generate
from db.connection import SessionLocal
from db.models import Constructor, Driver, Race, RaceResult


POINTS_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def _points_for_position(position: int | None) -> float:
    if position is None or position < 1 or position > len(POINTS_TABLE):
        return 0.0
    return float(POINTS_TABLE[position - 1])


def _actual_season_totals(
    db: Session, season_year: int
) -> tuple[dict[int, dict], dict[int, dict]]:
    """Return (driver_totals, constructor_totals) for the season, using the
    points stored on RaceResult so we honour any historical anomalies."""
    rows = db.execute(
        select(
            RaceResult.driver_id,
            RaceResult.constructor_id,
            RaceResult.race_id,
            RaceResult.points,
            Driver.code,
            Driver.surname,
            Constructor.name.label("constructor_name"),
        )
        .join(Driver, RaceResult.driver_id == Driver.id)
        .join(Constructor, RaceResult.constructor_id == Constructor.id)
        .join(Race, RaceResult.race_id == Race.id)
        .where(Race.season_year == season_year)
    ).all()

    drivers: dict[int, dict] = defaultdict(
        lambda: {"points": 0.0, "code": "?", "surname": "", "races": set()}
    )
    constructors: dict[int, dict] = defaultdict(
        lambda: {"points": 0.0, "name": "?"}
    )

    for row in rows:
        d = drivers[row.driver_id]
        d["points"] += float(row.points or 0)
        d["code"] = row.code or d["code"]
        d["surname"] = row.surname or d["surname"]
        d["races"].add(row.race_id)

        c = constructors[row.constructor_id]
        c["points"] += float(row.points or 0)
        c["name"] = row.constructor_name or c["name"]

    return drivers, constructors


def _race_points_per_driver(
    db: Session, race_id: int, code_to_driver_id: dict[str, int]
) -> tuple[dict[int, float], dict[int, int]]:
    """Actual points + actual final positions in {race_id}, keyed by driver_id."""
    rows = db.execute(
        select(
            RaceResult.driver_id,
            RaceResult.points,
            RaceResult.final_position,
        ).where(RaceResult.race_id == race_id)
    ).all()
    return (
        {r.driver_id: float(r.points or 0) for r in rows},
        {r.driver_id: int(r.final_position) for r in rows if r.final_position is not None},
    )


def _alternate_points_per_driver(
    alt_laps: list[dict], code_to_driver_id: dict[str, int]
) -> dict[int, float]:
    """Synthesize points from the alternate final-lap ordering using the
    standard F1 points table."""
    if not alt_laps:
        return {}
    final = alt_laps[-1]
    points: dict[int, float] = {}
    for driver in final["drivers"]:
        driver_id = code_to_driver_id.get(driver["code"])
        if driver_id is None:
            continue
        points[driver_id] = _points_for_position(driver["position"])
    return points


def _rank(rows: Iterable[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: r["points"], reverse=True)


def _narrative(
    season: int,
    race_name: str,
    actual_top3: list[dict],
    alt_top3: list[dict],
    actual_champion: str,
    alt_champion: str,
    delta_summary: list[str],
) -> str:
    if actual_champion == alt_champion:
        return (
            f"{race_name} ({season}) counterfactual still gives the title to "
            f"{actual_champion}. The standings shuffle but the championship "
            f"order at the top stays put."
        )

    headline = (
        f"If this counterfactual held in {race_name} ({season}), the "
        f"championship would have gone to {alt_champion} instead of "
        f"{actual_champion}."
    )
    body = " ".join(delta_summary)
    return f"{headline} {body}"


def compute_championship_impact(race_id: int, changes: list[dict]) -> dict:
    """Recompute end-of-season standings under a counterfactual race result."""
    with SessionLocal() as db:
        race = db.get(Race, race_id)
        if race is None or race.season_year is None:
            return {"error": "Race not found or missing season"}

        season = race.season_year
        actual_drivers, actual_constructors = _actual_season_totals(db, season)
        if not actual_drivers:
            return {
                "race_id": race_id,
                "season": season,
                "error": "No season results ingested yet.",
            }

        all_codes = db.execute(
            select(Driver.id, Driver.code).where(Driver.code.is_not(None))
        ).all()
        code_to_driver_id = {row.code: row.id for row in all_codes}

        driver_to_constructor: dict[int, int] = {}
        for row in db.execute(
            select(RaceResult.driver_id, RaceResult.constructor_id).where(
                RaceResult.race_id == race_id
            )
        ).all():
            if row.constructor_id is not None:
                driver_to_constructor[row.driver_id] = row.constructor_id

    simulated = simulate_counterfactual(race_id, changes)
    alt_laps = simulated.get("alt_laps", [])

    with SessionLocal() as db:
        actual_points_in_race, actual_positions = _race_points_per_driver(
            db, race_id, code_to_driver_id
        )

    alt_points_in_race = _alternate_points_per_driver(alt_laps, code_to_driver_id)

    alt_drivers = {
        driver_id: {**data, "races": set(data["races"])}
        for driver_id, data in actual_drivers.items()
    }
    alt_constructors = {
        ctor_id: dict(data) for ctor_id, data in actual_constructors.items()
    }

    deltas: dict[int, float] = {}
    for driver_id, alt_pts in alt_points_in_race.items():
        actual_pts = actual_points_in_race.get(driver_id, 0.0)
        delta = alt_pts - actual_pts
        if not delta:
            continue
        deltas[driver_id] = delta
        if driver_id in alt_drivers:
            alt_drivers[driver_id]["points"] += delta
        ctor_id = driver_to_constructor.get(driver_id)
        if ctor_id and ctor_id in alt_constructors:
            alt_constructors[ctor_id]["points"] += delta

    actual_ranked = _rank(
        [
            {
                "driver_id": did,
                "code": data["code"],
                "surname": data["surname"],
                "points": round(data["points"], 1),
            }
            for did, data in actual_drivers.items()
        ]
    )
    alt_ranked = _rank(
        [
            {
                "driver_id": did,
                "code": data["code"],
                "surname": data["surname"],
                "points": round(data["points"], 1),
                "delta": round(deltas.get(did, 0.0), 1),
            }
            for did, data in alt_drivers.items()
        ]
    )

    actual_constructor_ranked = _rank(
        [
            {"constructor_id": cid, "name": data["name"], "points": round(data["points"], 1)}
            for cid, data in actual_constructors.items()
        ]
    )
    alt_constructor_ranked = _rank(
        [
            {
                "constructor_id": cid,
                "name": data["name"],
                "points": round(data["points"], 1),
                "delta": round(data["points"] - actual_constructors[cid]["points"], 1),
            }
            for cid, data in alt_constructors.items()
        ]
    )

    actual_champion = actual_ranked[0]["code"] if actual_ranked else ""
    alt_champion = alt_ranked[0]["code"] if alt_ranked else ""
    title_changed = actual_champion != alt_champion

    big_movers = sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    code_lookup = {did: actual_drivers.get(did, {}).get("code", "?") for did, _ in big_movers}
    delta_summary = [
        f"{code_lookup[did]} {'+' if delta > 0 else ''}{int(delta)}pts"
        for did, delta in big_movers
    ]

    return {
        "race_id": race_id,
        "season": season,
        "race_name": race.name,
        "actual_champion": actual_champion,
        "alternate_champion": alt_champion,
        "championship_changed": title_changed,
        "actual_standings": actual_ranked[:10],
        "alternate_standings": alt_ranked[:10],
        "actual_constructor_standings": actual_constructor_ranked[:10],
        "alternate_constructor_standings": alt_constructor_ranked[:10],
        "biggest_movers": delta_summary,
        "narrative": _narrative(
            season,
            race.name or f"Race {race_id}",
            actual_ranked[:3],
            alt_ranked[:3],
            actual_champion,
            alt_champion,
            delta_summary,
        ),
    }
