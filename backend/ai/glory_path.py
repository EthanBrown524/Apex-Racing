"""Glory Path - the signature APEX feature.

Given a race and a target driver, find the minimum-cost set of counterfactual
changes that lifts that driver to their best plausible finishing position.

Approach is a hybrid:
  1. Deterministic analyzer scans the actual race to surface candidate
     interventions ranked by potential gain (slow pit stops, DNFs ahead,
     bad strategy windows, lost positions on lap 1).
  2. A greedy search applies the highest-leverage change, re-simulates with
     the existing counterfactual engine, and stops when:
       - target position reached, OR
       - 4 changes applied (caps narrative complexity), OR
       - no further gain in two consecutive iterations.
  3. Granite writes the closing storyline citing FIA / race-narrative context.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.counterfactual import simulate_counterfactual
from ai.granite import generate
from ai.rag import build_race_context
from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race, RaceResult


MAX_CHANGES = 4
MIN_GAIN_TO_CONTINUE = 1  # at least one position improved per step


def _driver_id_by_code(db: Session, code: str) -> Optional[int]:
    code = code.upper().strip()
    row = db.execute(select(Driver.id).where(Driver.code == code)).first()
    return row[0] if row else None


def _final_positions(alt_laps: list[dict]) -> dict[str, int]:
    if not alt_laps:
        return {}
    final = alt_laps[-1]
    return {d["code"]: d["position"] for d in final["drivers"]}


def _candidate_changes(db: Session, race_id: int, driver_code: str) -> list[dict]:
    driver_id = _driver_id_by_code(db, driver_code)
    if driver_id is None:
        return []

    candidates: list[dict] = []

    # 1) Slow pit stops we wish hadn't happened that slow (re-execute pit faster
    #    by moving it to a lap with safety car, if any - approximated with "pit
    #    timed earlier by 5 laps").
    pit_rows = db.execute(
        select(PitStop.lap, PitStop.duration_ms)
        .where(PitStop.race_id == race_id, PitStop.driver_id == driver_id)
        .order_by(PitStop.lap.asc())
    ).all()

    durations = [p.duration_ms for p in pit_rows if p.duration_ms]
    avg_pit = (sum(durations) / len(durations)) if durations else 25000
    for stop in pit_rows:
        if stop.duration_ms and stop.duration_ms > avg_pit * 1.15:
            candidates.append(
                {
                    "driver_code": driver_code,
                    "change_type": "pit_lap",
                    "lap": stop.lap,
                    "value": max(1, stop.lap - 3),
                    "_reason": f"Slow pit stop ({stop.duration_ms} ms vs avg {int(avg_pit)} ms); shift earlier",
                    "_expected_gain": 2,
                }
            )

    # 2) Drivers ahead at the finish who retired late in the actual race -
    #    these are already ahead by virtue of finishing; nothing to do.  But
    #    drivers ahead in the final classification we can challenge by giving
    #    *them* a DNF (light-touch intervention).
    result = (
        db.query(RaceResult)
        .filter(RaceResult.race_id == race_id, RaceResult.driver_id == driver_id)
        .one_or_none()
    )
    our_final = result.final_position if result else None

    ahead_codes: list[tuple[int, str]] = []
    if our_final and our_final > 1:
        rows = db.execute(
            select(RaceResult.final_position, Driver.code)
            .join(Driver, RaceResult.driver_id == Driver.id)
            .where(
                RaceResult.race_id == race_id,
                RaceResult.final_position < our_final,
            )
            .order_by(RaceResult.final_position.asc())
        ).all()
        ahead_codes = [(r.final_position, r.code) for r in rows if r.code]

    last_lap_row = db.execute(
        select(LapTime.lap)
        .where(LapTime.race_id == race_id, LapTime.driver_id == driver_id)
        .order_by(LapTime.lap.desc())
        .limit(1)
    ).first()
    final_lap = last_lap_row[0] if last_lap_row else 50

    for pos, code in ahead_codes[:3]:
        candidates.append(
            {
                "driver_code": code,
                "change_type": "dnf",
                "lap": max(5, int(final_lap * 0.6)),
                "value": None,
                "_reason": f"P{pos} {code} retires mid-race -> {driver_code} gains a place",
                "_expected_gain": 1,
            }
        )

    # 3) Fast lap nudge: if the driver actually has a slow lap during a stint,
    #    pretend it was a tenth quicker - small but useful for tie-breaks.
    slow_laps = db.execute(
        select(LapTime.lap, LapTime.time_ms)
        .where(
            LapTime.race_id == race_id,
            LapTime.driver_id == driver_id,
            LapTime.time_ms.is_not(None),
        )
        .order_by(LapTime.time_ms.desc())
        .limit(1)
    ).first()
    if slow_laps and slow_laps.time_ms:
        candidates.append(
            {
                "driver_code": driver_code,
                "change_type": "fastest_lap",
                "lap": slow_laps.lap,
                "value": int(slow_laps.time_ms * 0.93),
                "_reason": f"Recover the worst stint lap (L{slow_laps.lap})",
                "_expected_gain": 1,
            }
        )

    candidates.sort(key=lambda c: c["_expected_gain"], reverse=True)
    return candidates


def _strip_internal(change: dict) -> dict:
    return {k: v for k, v in change.items() if not k.startswith("_")}


def find_glory_path(race_id: int, driver_code: str, target_position: int = 1) -> dict:
    driver_code = driver_code.upper().strip()
    with SessionLocal() as db:
        race = db.get(Race, race_id)
        if race is None:
            return {
                "race_id": race_id,
                "driver_code": driver_code,
                "error": "Race not found",
            }
        candidates = _candidate_changes(db, race_id, driver_code)

    if not candidates:
        return {
            "race_id": race_id,
            "driver_code": driver_code,
            "applied": [],
            "starting_position": None,
            "achieved_position": None,
            "target_position": target_position,
            "explanation": "No candidate interventions surfaced for this driver - data may be missing.",
            "citations": [],
        }

    baseline = simulate_counterfactual(race_id, [])
    baseline_positions = _final_positions(baseline.get("alt_laps", []))
    starting_pos = baseline_positions.get(driver_code)

    applied: list[dict] = []
    current_positions = baseline_positions
    no_gain_streak = 0
    used = set()

    while len(applied) < MAX_CHANGES:
        current = current_positions.get(driver_code)
        if current is None or current <= target_position:
            break

        next_change = None
        for cand in candidates:
            key = (cand["change_type"], cand["driver_code"], cand["lap"])
            if key in used:
                continue
            next_change = cand
            used.add(key)
            break
        if next_change is None:
            break

        trial = applied + [_strip_internal(next_change)]
        result = simulate_counterfactual(race_id, trial)
        new_positions = _final_positions(result.get("alt_laps", []))
        new_pos = new_positions.get(driver_code)

        gained = (current - new_pos) if (current and new_pos) else 0
        if gained >= MIN_GAIN_TO_CONTINUE:
            applied = trial
            current_positions = new_positions
            no_gain_streak = 0
        else:
            no_gain_streak += 1
            if no_gain_streak >= 2:
                break

    achieved = current_positions.get(driver_code)

    rag = build_race_context(
        race_id=race_id,
        query=f"{driver_code} race story strategy mistakes safety car incidents",
    )
    prompt = f"""You are an F1 strategist. In 3-5 sentences, narrate the alternate storyline where {driver_code} finishes P{achieved} at the {race.name} ({race.season_year}) thanks to the following interventions. Reference the citations [n] where they support a claim. Do not invent any facts.

Starting (actual) position: P{starting_pos}
Achieved (alternate) position: P{achieved}
Target was: P{target_position}

Interventions applied (in order):
{chr(10).join('- ' + _describe_change(c) for c in applied) or '- (none)'}

Context:
{rag['context']}

Storyline:"""

    try:
        story = generate(prompt, max_new_tokens=350, temperature=0.55).strip()
    except Exception as exc:
        story = f"(Granite storyline unavailable: {exc})"

    reasons = []
    for change, cand in zip(applied, candidates):
        if cand.get("_reason"):
            reasons.append({"change": change, "rationale": cand["_reason"]})

    return {
        "race_id": race_id,
        "driver_code": driver_code,
        "target_position": target_position,
        "starting_position": starting_pos,
        "achieved_position": achieved,
        "applied": applied,
        "rationales": reasons,
        "explanation": story,
        "citations": rag["citations"],
    }


def _describe_change(c: dict) -> str:
    if c["change_type"] == "pit_lap":
        return f"{c['driver_code']} pit moved to lap {c.get('value')}"
    if c["change_type"] == "dnf":
        return f"{c['driver_code']} retires on lap {c.get('lap')}"
    if c["change_type"] == "fastest_lap":
        return f"{c['driver_code']} sets {c.get('value')} ms on lap {c.get('lap')}"
    return f"{c['driver_code']} {c['change_type']}"
