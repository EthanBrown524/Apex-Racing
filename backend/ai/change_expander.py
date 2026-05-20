"""Translate AI Race Director decisions into engine-readable change records.

The deterministic counterfactual engine understands 7 change types
(see ai.counterfactual). The Race Director emits decisions in a small
vocabulary - pit / stay_out / retire / push / manage. This module bridges
them.

Action mapping:
  pit       -> pit_lap change at the decision's lap
  retire    -> dnf change at the decision's lap
  push      -> fastest_lap change with -300ms vs the driver's average
  manage    -> mechanical change with +250ms/lap for 3 laps
                (modeled as a single mechanical record - the engine applies
                 the recurring penalty from `lap` onward; in practice this
                 also rolls back automatically when the driver next pits in
                 the user's primary changes)
  stay_out  -> no engine change (acts only as a flag for the narrative)
"""

from __future__ import annotations


PUSH_DELTA_MS = -300
MANAGE_PENALTY_MS = 250
MANAGE_DURATION = 3
FALLBACK_LAP_TIME_MS = 90_000


def expand_decision(decision: dict, baseline_lap_ms: int | None = None) -> dict | None:
    """Translate one Race Director decision into a single engine change
    record, or None if the action is a no-op (e.g. stay_out)."""
    action = decision.get("action")
    code = decision.get("driver_code", "").upper()
    lap = decision.get("lap")

    if not code or lap is None:
        return None

    if action == "pit":
        return {
            "driver_code": code,
            "change_type": "pit_lap",
            "lap": lap,
            "value": lap,
        }

    if action == "retire":
        return {
            "driver_code": code,
            "change_type": "dnf",
            "lap": lap,
            "value": None,
        }

    if action == "push":
        target = int((baseline_lap_ms or FALLBACK_LAP_TIME_MS) + PUSH_DELTA_MS)
        return {
            "driver_code": code,
            "change_type": "fastest_lap",
            "lap": lap,
            "value": target,
        }

    if action == "manage":
        return {
            "driver_code": code,
            "change_type": "mechanical",
            "lap": lap,
            "value": MANAGE_PENALTY_MS,
        }

    if action == "stay_out":
        return None

    return None


def expand_plan(plan: dict, baseline_laps_by_code: dict[str, int] | None = None) -> list[dict]:
    """Translate a Race Director plan into a list of engine changes.
    `baseline_laps_by_code` is a `{code: average_lap_time_ms}` map used for
    `push` action targets; falls back to FALLBACK_LAP_TIME_MS when missing.
    """
    expanded: list[dict] = []
    baseline_laps_by_code = baseline_laps_by_code or {}
    for decision in plan.get("decisions", []):
        code = decision.get("driver_code", "").upper()
        baseline = baseline_laps_by_code.get(code)
        change = expand_decision(decision, baseline_lap_ms=baseline)
        if change is None:
            continue
        change["_origin"] = "race_director"
        change["_rationale"] = decision.get("rationale", "")
        change["_confidence"] = decision.get("confidence", 0.5)
        change["_action"] = decision.get("action")
        expanded.append(change)
    return expanded


def expand_plans(
    plans: list[dict], baseline_laps_by_code: dict[str, int] | None = None
) -> list[dict]:
    out: list[dict] = []
    for plan in plans:
        out.extend(expand_plan(plan, baseline_laps_by_code))
    return out
