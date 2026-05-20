"""Driver skill profiles derived from historical race data.

Five ratings, all 0..1 except race_pace_index (relative to team-mate):

  - wet_skill         positions gained in safety-car-heavy races
  - tyre_management   average stint length normalized to race distance
  - aggression        average grid -> final position gain
  - consistency       1 - normalized lap-time variance
  - race_pace_index   ratio of finish-rate vs the rest of the field (1.0 = average)

These feed the Race Director prompt so Granite can reason about who would do
what in a counterfactual ("Hamilton's wet skill 0.92 lets him gamble").

When the database is empty or a driver has no history, every value defaults to
0.5 (race_pace_index 1.0) so the rest of the pipeline still works.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race, RaceResult, SafetyCar


DEFAULT_PROFILE = {
    "wet_skill": 0.5,
    "tyre_management": 0.5,
    "aggression": 0.5,
    "consistency": 0.5,
    "race_pace_index": 1.0,
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _build_for_race(db: Session, race: Race) -> dict[str, dict]:
    """Build profiles for every driver who started this race, using the
    season-to-date as the historical window."""
    if race.season_year is None or race.round is None:
        return {}

    drivers_in_race = db.execute(
        select(Driver.id, Driver.code, Driver.surname)
        .join(RaceResult, RaceResult.driver_id == Driver.id)
        .where(RaceResult.race_id == race.id)
    ).all()

    historical_race_ids = [
        r[0]
        for r in db.execute(
            select(Race.id)
            .where(
                (Race.season_year < race.season_year)
                | (
                    (Race.season_year == race.season_year)
                    & (Race.round < race.round)
                )
            )
            .order_by(Race.season_year.desc(), Race.round.desc())
            .limit(40)
        ).all()
    ]

    profiles: dict[str, dict] = {}
    if not historical_race_ids:
        for _, code, _ in drivers_in_race:
            if code:
                profiles[code] = {**DEFAULT_PROFILE, "code": code}
        return profiles

    races_with_sc = set(
        r[0]
        for r in db.execute(
            select(SafetyCar.race_id)
            .where(SafetyCar.race_id.in_(historical_race_ids))
            .distinct()
        ).all()
    )

    results = db.execute(
        select(
            RaceResult.driver_id,
            RaceResult.race_id,
            RaceResult.grid_position,
            RaceResult.final_position,
        ).where(RaceResult.race_id.in_(historical_race_ids))
    ).all()

    pit_counts = defaultdict(list)
    for row in db.execute(
        select(PitStop.driver_id, PitStop.race_id, func.count(PitStop.id))
        .where(PitStop.race_id.in_(historical_race_ids))
        .group_by(PitStop.driver_id, PitStop.race_id)
    ).all():
        pit_counts[row[0]].append(row[2])

    lap_variances: dict[int, float] = {}
    for row in db.execute(
        select(LapTime.driver_id, func.stddev_samp(LapTime.time_ms))
        .where(
            LapTime.race_id.in_(historical_race_ids), LapTime.time_ms.is_not(None)
        )
        .group_by(LapTime.driver_id)
    ).all():
        if row[1] is not None:
            lap_variances[row[0]] = float(row[1])

    grid_deltas: dict[int, list[int]] = defaultdict(list)
    sc_deltas: dict[int, list[int]] = defaultdict(list)
    finish_positions: dict[int, list[int]] = defaultdict(list)

    for row in results:
        if row.grid_position is None or row.final_position is None:
            continue
        delta = row.grid_position - row.final_position
        grid_deltas[row.driver_id].append(delta)
        finish_positions[row.driver_id].append(row.final_position)
        if row.race_id in races_with_sc:
            sc_deltas[row.driver_id].append(delta)

    median_variance = (
        sorted(lap_variances.values())[len(lap_variances) // 2]
        if lap_variances
        else None
    )

    for driver_id, code, _surname in drivers_in_race:
        if not code:
            continue
        profile = dict(DEFAULT_PROFILE)
        profile["code"] = code

        aggression_deltas = grid_deltas.get(driver_id, [])
        if aggression_deltas:
            avg_gain = sum(aggression_deltas) / len(aggression_deltas)
            profile["aggression"] = _clamp01(0.5 + avg_gain / 12.0)

        sc_gains = sc_deltas.get(driver_id, [])
        if sc_gains:
            avg_sc_gain = sum(sc_gains) / len(sc_gains)
            profile["wet_skill"] = _clamp01(0.5 + avg_sc_gain / 10.0)
        elif aggression_deltas:
            profile["wet_skill"] = _clamp01(profile["aggression"] * 0.9)

        pit_count_list = pit_counts.get(driver_id, [])
        if pit_count_list:
            avg_pits = sum(pit_count_list) / len(pit_count_list)
            profile["tyre_management"] = _clamp01(1.0 - (avg_pits - 1.0) / 4.0)

        variance = lap_variances.get(driver_id)
        if variance is not None and median_variance:
            profile["consistency"] = _clamp01(
                1.0 - (variance / (median_variance * 2.0))
            )

        finish_list = finish_positions.get(driver_id, [])
        if finish_list:
            avg_finish = sum(finish_list) / len(finish_list)
            profile["race_pace_index"] = round(
                max(0.5, min(1.5, (21 - avg_finish) / 10.0)), 3
            )

        profile["wet_skill"] = round(profile["wet_skill"], 2)
        profile["tyre_management"] = round(profile["tyre_management"], 2)
        profile["aggression"] = round(profile["aggression"], 2)
        profile["consistency"] = round(profile["consistency"], 2)

        profiles[code] = profile

    return profiles


def build_profiles_for_race(race_id: int) -> dict[str, dict]:
    """Public entry point; never raises."""
    try:
        with SessionLocal() as db:
            race = db.get(Race, race_id)
            if race is None:
                return {}
            return _build_for_race(db, race)
    except Exception:
        return {}


def summarize_profile_line(profile: dict) -> str:
    """One-line summary used in the Race Director prompt."""
    return (
        f"{profile.get('code', '???')}: "
        f"wet {profile.get('wet_skill', 0.5)}, "
        f"tyre {profile.get('tyre_management', 0.5)}, "
        f"aggr {profile.get('aggression', 0.5)}, "
        f"cons {profile.get('consistency', 0.5)}, "
        f"pace {profile.get('race_pace_index', 1.0)}"
    )
