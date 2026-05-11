from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race
from ai.granite import generate


def _load_baseline(db: Session, race_id: int) -> dict:
    """Load all lap times and pit stops for a race into memory."""
    race = db.get(Race, race_id)
    if race is None:
        raise ValueError(f"Race {race_id} not found")

    pit_rows = db.execute(
        select(PitStop.driver_id, PitStop.lap, PitStop.duration_ms).where(
            PitStop.race_id == race_id
        )
    ).all()
    pit_lookup: dict[tuple[int, int], int | None] = {
        (driver_id, lap): duration_ms for driver_id, lap, duration_ms in pit_rows
    }

    rows = db.execute(
        select(LapTime, Driver.code, Driver.driver_ref)
        .join(Driver, LapTime.driver_id == Driver.id)
        .where(LapTime.race_id == race_id)
        .order_by(LapTime.lap.asc(), LapTime.position.asc())
    ).all()

    drivers_by_id: dict[int, str] = {}
    laps_by_driver: dict[int, list[dict]] = defaultdict(list)

    for lap_time, code, driver_ref in rows:
        driver_code = code or driver_ref[:3].upper()
        drivers_by_id[lap_time.driver_id] = driver_code
        laps_by_driver[lap_time.driver_id].append(
            {
                "lap": lap_time.lap,
                "time_ms": lap_time.time_ms,
                "position": lap_time.position,
                "gap_ms": lap_time.gap_to_leader_ms,
                "in_pit": (lap_time.driver_id, lap_time.lap) in pit_lookup,
                "pit_duration_ms": pit_lookup.get((lap_time.driver_id, lap_time.lap)),
            }
        )

    return {
        "race": race,
        "drivers_by_id": drivers_by_id,
        "laps_by_driver": laps_by_driver,
        "pit_lookup": pit_lookup,
    }


def _average_pit_duration_ms(pit_lookup: dict) -> int:
    """Calculate average pit stop duration across all stops."""
    durations = [d for d in pit_lookup.values() if d is not None and d > 0]
    if not durations:
        return 25000
    return int(sum(durations) / len(durations))


def _apply_changes(baseline: dict, changes: list[dict]) -> dict[int, list[dict]]:
    laps_by_driver: dict[int, list[dict]] = {
        driver_id: [lap.copy() for lap in laps]
        for driver_id, laps in baseline["laps_by_driver"].items()
    }
    drivers_by_id = baseline["drivers_by_id"]
    avg_pit_ms = _average_pit_duration_ms(baseline["pit_lookup"])
    code_to_id = {code: driver_id for driver_id, code in drivers_by_id.items()}

    for change in changes:
        driver_code = change.get("driver_code", "").upper()
        change_type = change.get("change_type")
        target_lap = change.get("lap")
        value = change.get("value")

        driver_id = code_to_id.get(driver_code)
        if driver_id is None:
            continue

        driver_laps = laps_by_driver.get(driver_id, [])

        if change_type == "pit_lap":
            new_pit_lap = int(value) if value is not None else target_lap
            if new_pit_lap is None:
                continue
            for lap in driver_laps:
                if lap["in_pit"]:
                    lap["time_ms"] = (lap["time_ms"] or 0) - avg_pit_ms
                    lap["in_pit"] = False
                    lap["pit_duration_ms"] = None
            for lap in driver_laps:
                if lap["lap"] == new_pit_lap:
                    lap["time_ms"] = (lap["time_ms"] or 0) + avg_pit_ms
                    lap["in_pit"] = True
                    lap["pit_duration_ms"] = avg_pit_ms
                    break

        elif change_type == "dnf":
            dnf_lap = target_lap or 1
            laps_by_driver[driver_id] = [
                lap for lap in driver_laps if lap["lap"] < dnf_lap
            ]

        elif change_type == "fastest_lap":
            target_time_ms = int(value) if value is not None else None
            if target_time_ms is None or target_lap is None:
                continue
            for lap in driver_laps:
                if lap["lap"] == target_lap:
                    lap["time_ms"] = target_time_ms
                    break

    return laps_by_driver


def _recompute_positions(
    laps_by_driver: dict[int, list[dict]],
    drivers_by_id: dict[int, str],
    total_laps: int,
) -> list[dict]:
    cumulative: dict[int, int] = {driver_id: 0 for driver_id in laps_by_driver}
    lap_snapshots: dict[int, dict[int, dict]] = defaultdict(dict)

    all_lap_numbers = sorted(
        {lap["lap"] for laps in laps_by_driver.values() for lap in laps}
    )

    for lap_num in all_lap_numbers:
        for driver_id, laps in laps_by_driver.items():
            lap = next((l for l in laps if l["lap"] == lap_num), None)
            if lap is None or lap.get("time_ms") is None:
                continue
            cumulative[driver_id] = cumulative.get(driver_id, 0) + lap["time_ms"]
            lap_snapshots[lap_num][driver_id] = {
                "driver_id": driver_id,
                "code": drivers_by_id.get(driver_id, "???"),
                "time_ms": lap["time_ms"],
                "cumulative_ms": cumulative[driver_id],
                "in_pit": lap.get("in_pit", False),
            }

    alt_laps = []
    for lap_num in all_lap_numbers:
        snapshot = lap_snapshots[lap_num]
        ranked = sorted(snapshot.values(), key=lambda d: d["cumulative_ms"])
        leader_ms = ranked[0]["cumulative_ms"] if ranked else 0

        drivers_out = []
        for position, driver in enumerate(ranked, start=1):
            drivers_out.append(
                {
                    "driver_id": driver["driver_id"],
                    "code": driver["code"],
                    "position": position,
                    "time_ms": driver["time_ms"],
                    "gap_ms": driver["cumulative_ms"] - leader_ms,
                    "in_pit": driver["in_pit"],
                }
            )

        alt_laps.append({"lap": lap_num, "drivers": drivers_out})

    return alt_laps


def _build_granite_prompt(
    race_name: str,
    changes: list[dict],
    change_summary: list[str],
    actual_top5: list[str],
    alt_top5: list[str],
) -> str:
    changes_text = ", ".join(change_summary) if change_summary else "no changes"
    actual_text = ", ".join(
        f"P{i+1} {code}" for i, code in enumerate(actual_top5)
    )
    alt_text = ", ".join(
        f"P{i+1} {code}" for i, code in enumerate(alt_top5)
    )

    return f"""You are an expert Formula 1 race analyst. Based only on the facts provided below, write a concise 2-3 sentence explanation of how the strategy change affected the race outcome. Do not invent any facts not provided.

Race: {race_name}
Strategy change applied: {changes_text}
Actual final top 5: {actual_text}
Alternate final top 5 (after change): {alt_text}

Explanation:"""


def _get_top5(laps: list[dict]) -> list[str]:
    """Get top 5 driver codes from the final lap."""
    if not laps:
        return []
    final_lap = laps[-1]
    sorted_drivers = sorted(final_lap["drivers"], key=lambda d: d["position"])
    return [d["code"] for d in sorted_drivers[:5]]


def simulate_counterfactual(race_id: int, changes: list[dict]) -> dict:
    """
    Run a deterministic counterfactual simulation and generate
    a Granite AI explanation of the result.
    """
    db = SessionLocal()
    try:
        baseline = _load_baseline(db, race_id)
        modified_laps = _apply_changes(baseline, changes)
        alt_laps = _recompute_positions(
            modified_laps,
            baseline["drivers_by_id"],
            baseline["race"].total_laps or 0,
        )

        # Build change summary
        change_summary = []
        for c in changes:
            if c["change_type"] == "pit_lap":
                change_summary.append(
                    f"{c['driver_code']} pit moved to lap {c['value']}"
                )
            elif c["change_type"] == "dnf":
                change_summary.append(
                    f"{c['driver_code']} retired from lap {c['lap']}"
                )
            elif c["change_type"] == "fastest_lap":
                change_summary.append(
                    f"{c['driver_code']} set {c['value']}ms on lap {c['lap']}"
                )

        # Get actual vs alternate top 5 from final lap
        race = baseline["race"]

        # Load actual final lap top 5 from baseline laps_by_driver
        actual_final_positions = {}
        for driver_id, laps in baseline["laps_by_driver"].items():
            if laps:
                last_lap = laps[-1]
                actual_final_positions[last_lap["position"]] = baseline[
                    "drivers_by_id"
                ].get(driver_id, "???")
        actual_top5 = [
            actual_final_positions[p]
            for p in sorted(actual_final_positions.keys())[:5]
            if p in actual_final_positions
        ]

        alt_top5 = _get_top5(alt_laps)

        # Generate Granite explanation
        explanation = "Simulation complete."
        try:
            prompt = _build_granite_prompt(
                race_name=race.name or "Unknown Race",
                changes=changes,
                change_summary=change_summary,
                actual_top5=actual_top5,
                alt_top5=alt_top5,
            )
            granite_response = generate(prompt, max_new_tokens=200, temperature=0.5)
            # Take only the first 3 sentences
            sentences = granite_response.strip().split(".")
            explanation = ". ".join(s.strip() for s in sentences[:3] if s.strip()) + "."
        except Exception as granite_err:
            explanation = (
                f"Simulation complete. Granite explanation unavailable: {granite_err}"
            )

        return {
            "race_id": race_id,
            "alt_laps": alt_laps,
            "changes": changes,
            "summary": change_summary,
            "explanation": explanation,
        }

    except ValueError as exc:
        return {
            "race_id": race_id,
            "alt_laps": [],
            "changes": changes,
            "summary": [],
            "explanation": str(exc),
        }
    finally:
        db.close()