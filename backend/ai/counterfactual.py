"""Counterfactual race simulator.

Supported change types:
    pit_lap        - move a driver's pit stop to a different lap
    dnf            - driver retires on a given lap
    fastest_lap    - rewrite a single lap's time
    mechanical     - small recurring time loss starting from lap N (sec/lap)
    weather        - global tire-temp shift; pace penalty applied to all drivers
                     except those whose code is listed in value['benefits']
    safety_car     - inject (or remove) a safety car window; pit gain/loss is
                     re-bucketed for everyone pitting in the window
    grid_swap      - swap two drivers' starting positions; carries through as
                     a constant time delta until each next pit window
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.granite import generate
from ai.rag import build_race_context
from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race, SafetyCar


WEATHER_PENALTY_MS = 1200
MECHANICAL_PENALTY_MS = 800
SC_PIT_SAVINGS_MS = 12000
GRID_DELTA_MS = 350


def _load_baseline(db: Session, race_id: int) -> dict:
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

    sc_rows = db.execute(
        select(SafetyCar.type, SafetyCar.lap_start, SafetyCar.lap_end).where(
            SafetyCar.race_id == race_id
        )
    ).all()
    safety_cars = [
        {"type": tp, "lap_start": ls, "lap_end": le} for tp, ls, le in sc_rows
    ]

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
        "safety_cars": safety_cars,
    }


def _average_pit_duration_ms(pit_lookup: dict) -> int:
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
        change_type = change.get("change_type")
        target_lap = change.get("lap")
        value = change.get("value")
        driver_code = (change.get("driver_code") or "").upper()
        driver_id = code_to_id.get(driver_code)

        if change_type == "pit_lap" and driver_id is not None:
            _apply_pit_lap(laps_by_driver[driver_id], target_lap, value, avg_pit_ms)

        elif change_type == "dnf" and driver_id is not None:
            dnf_lap = target_lap or 1
            laps_by_driver[driver_id] = [
                lap for lap in laps_by_driver[driver_id] if lap["lap"] < dnf_lap
            ]

        elif change_type == "fastest_lap" and driver_id is not None:
            target_time_ms = _safe_int(value)
            if target_time_ms is None or target_lap is None:
                continue
            for lap in laps_by_driver[driver_id]:
                if lap["lap"] == target_lap:
                    lap["time_ms"] = target_time_ms
                    break

        elif change_type == "mechanical" and driver_id is not None:
            start_lap = target_lap or 1
            severity = _safe_int(value) or MECHANICAL_PENALTY_MS
            for lap in laps_by_driver[driver_id]:
                if lap["lap"] >= start_lap and lap["time_ms"] is not None:
                    lap["time_ms"] += severity

        elif change_type == "weather":
            benefits = set()
            penalty = WEATHER_PENALTY_MS
            if isinstance(value, dict):
                benefits = {c.upper() for c in value.get("benefits", [])}
                penalty = int(value.get("penalty_ms", WEATHER_PENALTY_MS))
            for d_id, laps in laps_by_driver.items():
                code = drivers_by_id.get(d_id, "")
                if code in benefits:
                    continue
                for lap in laps:
                    if (target_lap is None or lap["lap"] >= target_lap) and lap[
                        "time_ms"
                    ] is not None:
                        lap["time_ms"] += penalty

        elif change_type == "safety_car":
            start = _safe_int(value) or (target_lap or 10)
            end = start + 3
            for d_id, laps in laps_by_driver.items():
                for lap in laps:
                    if start <= lap["lap"] <= end and lap.get("in_pit"):
                        lap["time_ms"] = (lap["time_ms"] or 0) - SC_PIT_SAVINGS_MS

        elif change_type == "grid_swap":
            partner_code = (value or "").upper() if isinstance(value, str) else ""
            partner_id = code_to_id.get(partner_code)
            if partner_id is None or driver_id is None:
                continue
            switch_lap = target_lap or 6
            for lap in laps_by_driver[driver_id]:
                if lap["lap"] <= switch_lap and lap["time_ms"] is not None:
                    lap["time_ms"] -= GRID_DELTA_MS
            for lap in laps_by_driver[partner_id]:
                if lap["lap"] <= switch_lap and lap["time_ms"] is not None:
                    lap["time_ms"] += GRID_DELTA_MS

    return laps_by_driver


def _apply_pit_lap(driver_laps: list[dict], target_lap, value, avg_pit_ms: int) -> None:
    new_pit_lap = _safe_int(value) or _safe_int(target_lap)
    if new_pit_lap is None:
        return
    for lap in driver_laps:
        if lap.get("in_pit"):
            lap["time_ms"] = (lap["time_ms"] or 0) - avg_pit_ms
            lap["in_pit"] = False
            lap["pit_duration_ms"] = None
    for lap in driver_laps:
        if lap["lap"] == new_pit_lap:
            lap["time_ms"] = (lap["time_ms"] or 0) + avg_pit_ms
            lap["in_pit"] = True
            lap["pit_duration_ms"] = avg_pit_ms
            break


def _safe_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


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


def _describe_change(c: dict) -> str:
    ct = c.get("change_type")
    dc = c.get("driver_code", "")
    lap = c.get("lap")
    val = c.get("value")
    if ct == "pit_lap":
        return f"{dc} pit moved to lap {val}"
    if ct == "dnf":
        return f"{dc} retires on lap {lap}"
    if ct == "fastest_lap":
        return f"{dc} sets {val} ms on lap {lap}"
    if ct == "mechanical":
        return f"{dc} mechanical issue from lap {lap} (+{val or MECHANICAL_PENALTY_MS} ms/lap)"
    if ct == "weather":
        benefits = (val or {}).get("benefits", []) if isinstance(val, dict) else []
        return f"weather window from lap {lap}; favours {','.join(benefits) or 'none'}"
    if ct == "safety_car":
        return f"safety car lap {val or lap}"
    if ct == "grid_swap":
        return f"{dc} swaps grid with {val}"
    return f"{dc} {ct}"


def _build_granite_prompt(
    race_name: str,
    change_summary: list[str],
    actual_top5: list[str],
    alt_top5: list[str],
    context: str,
) -> str:
    changes_text = "; ".join(change_summary) if change_summary else "no changes"
    actual_text = ", ".join(f"P{i+1} {code}" for i, code in enumerate(actual_top5))
    alt_text = ", ".join(f"P{i+1} {code}" for i, code in enumerate(alt_top5))

    return f"""You are an expert Formula 1 race analyst. Write a 3-4 sentence explanation of how the strategy change altered the race outcome. Reference the retrieved race context using [n] citations where relevant. Use ONLY the facts provided.

Race: {race_name}
Strategy change applied: {changes_text}
Actual final top 5: {actual_text}
Alternate final top 5: {alt_text}

Context:
{context}

Explanation:"""


def _get_top5(laps: list[dict]) -> list[str]:
    if not laps:
        return []
    final_lap = laps[-1]
    sorted_drivers = sorted(final_lap["drivers"], key=lambda d: d["position"])
    return [d["code"] for d in sorted_drivers[:5]]


def simulate_counterfactual(race_id: int, changes: list[dict]) -> dict:
    db = SessionLocal()
    try:
        baseline = _load_baseline(db, race_id)
        modified_laps = _apply_changes(baseline, changes)
        alt_laps = _recompute_positions(
            modified_laps,
            baseline["drivers_by_id"],
            baseline["race"].total_laps or 0,
        )

        change_summary = [_describe_change(c) for c in changes]

        actual_final_positions = {}
        for driver_id, laps in baseline["laps_by_driver"].items():
            if laps:
                last_lap = laps[-1]
                actual_final_positions[last_lap["position"]] = baseline["drivers_by_id"].get(
                    driver_id, "???"
                )
        actual_top5 = [
            actual_final_positions[p]
            for p in sorted(actual_final_positions.keys())[:5]
            if p in actual_final_positions
        ]
        alt_top5 = _get_top5(alt_laps)

        rag_query = (
            f"counterfactual: {', '.join(change_summary)}" if change_summary else "race overview"
        )
        rag = build_race_context(race_id=race_id, query=rag_query)

        explanation = "Simulation complete."
        try:
            prompt = _build_granite_prompt(
                race_name=baseline["race"].name or "Unknown Race",
                change_summary=change_summary,
                actual_top5=actual_top5,
                alt_top5=alt_top5,
                context=rag["context"],
            )
            granite_response = generate(prompt, max_new_tokens=300, temperature=0.5)
            sentences = granite_response.strip().split(".")
            explanation = ". ".join(s.strip() for s in sentences[:4] if s.strip()) + "."
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
            "citations": rag["citations"],
            "actual_top5": actual_top5,
            "alt_top5": alt_top5,
        }

    except ValueError as exc:
        return {
            "race_id": race_id,
            "alt_laps": [],
            "changes": changes,
            "summary": [],
            "explanation": str(exc),
            "citations": [],
            "actual_top5": [],
            "alt_top5": [],
        }
    finally:
        db.close()
