"""AI Race Director - Granite plans the strategic responses other drivers
would make to a counterfactual trigger.

Pipeline (called from ai.counterfactual.simulate_counterfactual when
ai_director=True):

  1. Build driver profiles for the race (ai.driver_profiles)
  2. For each primary "trigger" change the user submitted, ask Granite to
     produce a structured JSON plan of how OTHER drivers respond
  3. Schema-validate the JSON
  4. Hand the validated decisions to ai.change_expander which converts them
     into engine-readable change records

Granite output is gracefully degraded: if the JSON is malformed or missing,
we return an empty plan and the deterministic engine runs on the user's
original changes only. The demo never breaks.
"""

from __future__ import annotations

import json

from ai.driver_profiles import build_profiles_for_race, summarize_profile_line
from ai.granite import generate


VALID_ACTIONS = {"pit", "stay_out", "retire", "push", "manage"}
MAX_DECISIONS = 8


def _trigger_summary(change: dict) -> str:
    ct = change.get("change_type")
    lap = change.get("lap")
    val = change.get("value")
    if ct == "weather":
        benefits = (val or {}).get("benefits", []) if isinstance(val, dict) else []
        return (
            f"Weather window from lap {lap} (potential rain). "
            f"Drivers possibly favoured: {','.join(benefits) or 'none specified'}."
        )
    if ct == "safety_car":
        return f"Safety car deployed at lap {val or lap}; field bunches up."
    if ct == "mechanical":
        return f"{change.get('driver_code')} hit a mechanical issue from lap {lap}."
    if ct == "dnf":
        return f"{change.get('driver_code')} retires on lap {lap}; their position is up for grabs."
    return ""


def _is_strategic_trigger(change: dict) -> bool:
    return change.get("change_type") in {"weather", "safety_car", "mechanical", "dnf"}


def _build_prompt(
    race_name: str,
    trigger_text: str,
    profiles: dict[str, dict],
) -> str:
    if not profiles:
        return ""

    sample = list(profiles.values())[:14]
    profile_lines = "\n".join(summarize_profile_line(p) for p in sample)

    return f"""You are the Race Director for a Formula 1 simulator. A trigger event has occurred. Decide how each driver would strategically respond, using their skill profile.

Race: {race_name}
Trigger: {trigger_text}

Driver profiles (0-1 scale; race_pace_index 0.5=back, 1.0=mid, 1.5=front):
{profile_lines}

Output rules:
- Reply with VALID JSON ONLY, no preamble, no markdown.
- Field "decisions" is a list of at most {MAX_DECISIONS} items.
- Each decision has: driver_code (3 letters), action, lap (int), confidence (0..1), rationale (one sentence).
- action MUST be one of: pit, stay_out, retire, push, manage.
- Use the driver's profile in your rationale (e.g., "high wet_skill lets HAM gamble").
- Do not invent driver codes. Use only codes from the profiles above.
- Only include drivers whose strategy you genuinely think shifts because of the trigger.

JSON schema:
{{"trigger_summary": "...", "decisions": [{{"driver_code": "...", "action": "pit", "lap": 26, "confidence": 0.8, "rationale": "..."}}], "narrative": "..."}}

JSON:"""


def _extract_json(text: str) -> dict | None:
    """Find the first balanced top-level JSON object in the text and parse it.
    Tolerant of preamble, markdown code fences, and trailing junk."""
    if not text:
        return None

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[-1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    snippet = cleaned[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def _validate_plan(plan: dict, profiles: dict[str, dict]) -> dict:
    """Return a sanitized plan: drop malformed decisions, clamp values, keep
    only known driver codes and valid actions."""
    if not isinstance(plan, dict):
        return {"decisions": [], "narrative": "", "trigger_summary": ""}

    decisions = plan.get("decisions") or []
    if not isinstance(decisions, list):
        decisions = []

    valid: list[dict] = []
    for entry in decisions[: MAX_DECISIONS * 2]:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("driver_code", "")).upper().strip()[:3]
        action = str(entry.get("action", "")).lower().strip()
        if not code or code not in profiles or action not in VALID_ACTIONS:
            continue
        try:
            lap = int(entry.get("lap"))
        except (TypeError, ValueError):
            lap = 1
        try:
            confidence = float(entry.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        rationale = str(entry.get("rationale", "")).strip()[:300]
        valid.append(
            {
                "driver_code": code,
                "action": action,
                "lap": max(1, lap),
                "confidence": round(confidence, 2),
                "rationale": rationale,
            }
        )
        if len(valid) >= MAX_DECISIONS:
            break

    return {
        "trigger_summary": str(plan.get("trigger_summary", "")).strip()[:300],
        "narrative": str(plan.get("narrative", "")).strip()[:600],
        "decisions": valid,
    }


def plan_response(race_id: int, race_name: str, trigger: dict) -> dict:
    """Return a validated plan for one trigger. Returns an empty plan when
    Granite is unavailable or the response is malformed."""
    profiles = build_profiles_for_race(race_id)
    if not profiles:
        return {"trigger_summary": "", "decisions": [], "narrative": "", "profiles": {}}

    trigger_text = _trigger_summary(trigger)
    if not trigger_text:
        return {"trigger_summary": "", "decisions": [], "narrative": "", "profiles": profiles}

    prompt = _build_prompt(race_name, trigger_text, profiles)
    if not prompt:
        return {"trigger_summary": "", "decisions": [], "narrative": "", "profiles": profiles}

    try:
        raw = generate(prompt, max_new_tokens=600, temperature=0.4)
    except Exception:
        return {
            "trigger_summary": trigger_text,
            "decisions": [],
            "narrative": "(Race Director unavailable; deterministic baseline applied.)",
            "profiles": profiles,
        }

    parsed = _extract_json(raw)
    if parsed is None:
        return {
            "trigger_summary": trigger_text,
            "decisions": [],
            "narrative": "(Race Director response could not be parsed; deterministic baseline applied.)",
            "profiles": profiles,
        }

    validated = _validate_plan(parsed, profiles)
    if not validated["trigger_summary"]:
        validated["trigger_summary"] = trigger_text
    validated["profiles"] = profiles
    return validated


def plan_for_changes(race_id: int, race_name: str, changes: list[dict]) -> list[dict]:
    """Plan responses for every strategic trigger in the change set.
    Non-strategic changes (pit_lap, fastest_lap, grid_swap) are skipped."""
    plans: list[dict] = []
    for change in changes:
        if not _is_strategic_trigger(change):
            continue
        plan = plan_response(race_id, race_name, change)
        plan["origin_change"] = change
        plans.append(plan)
    return plans
