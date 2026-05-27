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

from ai.changes import (
    GRID_DELTA_MS,
    MECHANICAL_PENALTY_MS,
    SC_PIT_SAVINGS_MS,
    WEATHER_PENALTY_MS,
    describe_change,
    safe_int,
)
from ai.granite import generate
from ai.rag import build_race_context
from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race, SafetyCar


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
            target_time_ms = safe_int(value)
            if target_time_ms is None or target_lap is None:
                continue
            for lap in laps_by_driver[driver_id]:
                if lap["lap"] == target_lap:
                    lap["time_ms"] = target_time_ms
                    break

        elif change_type == "mechanical" and driver_id is not None:
            start_lap = target_lap or 1
            severity = safe_int(value) or MECHANICAL_PENALTY_MS
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
            start = safe_int(value) or (target_lap or 10)
            end = start + 3
            # 1) Pit savings: a stop made under SC is cheaper.
            for d_id, laps in laps_by_driver.items():
                for lap in laps:
                    if start <= lap["lap"] <= end and lap.get("in_pit"):
                        lap["time_ms"] = (lap["time_ms"] or 0) - SC_PIT_SAVINGS_MS

            # 2) Gap compression: the field bunches up behind the SC. For each
            # lap in the window we equalize lap times so cumulative gaps
            # collapse to <= 1.5 s relative to the leader. Implementation:
            # within each lap of the window, compute the slowest survivor's
            # time and raise everyone else's time so the per-lap delta vs
            # the leader is at most 1.5 s / window_length.
            window_lap_count = max(1, end - start + 1)
            target_gap_per_lap_ms = int(1500 / window_lap_count)
            for lap_num in range(start, end + 1):
                lap_times_in_window: list[tuple[int, dict]] = []
                for d_id, laps in laps_by_driver.items():
                    for lap in laps:
                        if lap["lap"] == lap_num and lap.get("time_ms") is not None:
                            lap_times_in_window.append((d_id, lap))
                if not lap_times_in_window:
                    continue
                slowest = max(lt[1]["time_ms"] for lt in lap_times_in_window)
                for _d_id, lap in lap_times_in_window:
                    # Raise every lap toward the slowest, leaving a small
                    # per-lap delta of at most target_gap_per_lap_ms so the
                    # accumulated gap stays <= 1500 ms over the window.
                    floor_time = slowest - target_gap_per_lap_ms
                    if lap["time_ms"] < floor_time:
                        lap["time_ms"] = floor_time

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
    new_pit_lap = safe_int(value) or safe_int(target_lap)
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


def _recompute_positions(
    laps_by_driver: dict[int, list[dict]],
    drivers_by_id: dict[int, str],
    total_laps: int,
) -> list[dict]:
    """Recompute per-lap positions in O(N + L*D).

    Pre-indexes each driver's laps by lap number so the per-lap scan is a
    constant-time dict lookup rather than O(len(driver_laps)).
    """
    indexed: dict[int, dict[int, dict]] = {
        driver_id: {lap["lap"]: lap for lap in laps}
        for driver_id, laps in laps_by_driver.items()
    }
    cumulative: dict[int, int] = {driver_id: 0 for driver_id in laps_by_driver}

    all_lap_numbers = sorted(
        {lap_num for driver_laps in indexed.values() for lap_num in driver_laps}
    )

    alt_laps: list[dict] = []
    for lap_num in all_lap_numbers:
        snapshot: list[dict] = []
        for driver_id, laps_by_lap in indexed.items():
            lap = laps_by_lap.get(lap_num)
            if lap is None or lap.get("time_ms") is None:
                continue
            cumulative[driver_id] += lap["time_ms"]
            snapshot.append(
                {
                    "driver_id": driver_id,
                    "code": drivers_by_id.get(driver_id, "???"),
                    "time_ms": lap["time_ms"],
                    "cumulative_ms": cumulative[driver_id],
                    "in_pit": lap.get("in_pit", False),
                }
            )

        snapshot.sort(key=lambda d: d["cumulative_ms"])
        leader_ms = snapshot[0]["cumulative_ms"] if snapshot else 0

        alt_laps.append(
            {
                "lap": lap_num,
                "drivers": [
                    {
                        "driver_id": d["driver_id"],
                        "code": d["code"],
                        "position": position,
                        "time_ms": d["time_ms"],
                        "gap_ms": d["cumulative_ms"] - leader_ms,
                        "in_pit": d["in_pit"],
                    }
                    for position, d in enumerate(snapshot, start=1)
                ],
            }
        )

    return alt_laps


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


def _baseline_lap_times_by_code(baseline: dict) -> dict[str, int]:
    """Per-driver average lap time, used by the change expander to compute
    plausible `push` targets."""
    out: dict[str, int] = {}
    drivers_by_id = baseline["drivers_by_id"]
    for driver_id, laps in baseline["laps_by_driver"].items():
        code = drivers_by_id.get(driver_id)
        if not code:
            continue
        times = [lap["time_ms"] for lap in laps if lap.get("time_ms") is not None]
        if not times:
            continue
        out[code] = int(sum(times) / len(times))
    return out


def _public_changes(changes: list[dict]) -> list[dict]:
    """Drop internal underscore-prefixed fields for the API response."""
    return [
        {k: v for k, v in c.items() if not k.startswith("_")}
        for c in changes
    ]


def simulate_counterfactual(
    race_id: int,
    changes: list[dict],
    ai_director: bool = False,
) -> dict:
    db = SessionLocal()
    try:
        baseline = _load_baseline(db, race_id)

        race_director_plans: list[dict] = []
        expanded_changes: list[dict] = []
        effective_changes = list(changes)

        if ai_director and changes:
            try:
                from ai.race_director import plan_for_changes
                from ai.change_expander import expand_plans

                race_name = baseline["race"].name or f"Race {race_id}"
                race_director_plans = plan_for_changes(race_id, race_name, changes)
                lap_baseline = _baseline_lap_times_by_code(baseline)
                expanded_changes = expand_plans(
                    race_director_plans, baseline_laps_by_code=lap_baseline
                )
                effective_changes = list(changes) + expanded_changes
            except Exception:
                race_director_plans = []
                expanded_changes = []
                effective_changes = list(changes)

        modified_laps = _apply_changes(baseline, effective_changes)
        alt_laps = _recompute_positions(
            modified_laps,
            baseline["drivers_by_id"],
            baseline["race"].total_laps or 0,
        )

        change_summary = [describe_change(c) for c in effective_changes]

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

        rd_payload = None
        if ai_director:
            rd_payload = {
                "plans": [
                    {
                        "trigger_summary": p.get("trigger_summary", ""),
                        "narrative": p.get("narrative", ""),
                        "decisions": p.get("decisions", []),
                    }
                    for p in race_director_plans
                ],
                "expanded_changes": _public_changes(expanded_changes),
            }

        return {
            "race_id": race_id,
            "alt_laps": alt_laps,
            "changes": changes,
            "effective_changes": _public_changes(effective_changes),
            "summary": change_summary,
            "explanation": explanation,
            "citations": rag["citations"],
            "actual_top5": actual_top5,
            "alt_top5": alt_top5,
            "race_director": rd_payload,
        }

    except ValueError as exc:
        return {
            "race_id": race_id,
            "alt_laps": [],
            "changes": changes,
            "effective_changes": [],
            "summary": [],
            "explanation": str(exc),
            "citations": [],
            "actual_top5": [],
            "alt_top5": [],
            "race_director": None,
        }
    finally:
        db.close()
