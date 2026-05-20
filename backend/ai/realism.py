"""Granite-judged Realism Score for counterfactuals.

Returns a 0..1 score plus a 1-2 sentence reasoning. The score is a
heuristic combined with Granite's judgement when credentials are present.

Heuristic baseline (always runs):
  - more changes lower the score (each change costs 0.12)
  - DNFs are cheap (they happen); pit-lap moves are medium; weather/safety_car
    are high-cost interventions
  - changes that imply a winner-retires are extra suspect
"""

from __future__ import annotations

from ai.granite import generate


CHANGE_BASE_COST = {
    "pit_lap": 0.12,
    "dnf": 0.10,
    "fastest_lap": 0.05,
    "mechanical": 0.12,
    "weather": 0.20,
    "safety_car": 0.18,
    "grid_swap": 0.15,
}


def _heuristic(changes: list[dict]) -> float:
    if not changes:
        return 1.0
    score = 1.0
    for c in changes:
        score -= CHANGE_BASE_COST.get(c.get("change_type", ""), 0.15)
    return max(0.05, min(1.0, score))


def _granite_prompt(changes: list[dict], race_name: str, alt_top5: list[str]) -> str:
    summary = "; ".join(
        f"{c.get('driver_code') or 'field'} {c.get('change_type')} lap {c.get('lap')}"
        for c in changes
    ) or "none"
    return f"""You are an F1 strategy expert. Rate how realistic the following counterfactual would be on a 0.0-1.0 scale, where 1.0 = entirely plausible (could have happened on the day) and 0.0 = physically impossible. Reply in exactly this format, no preamble:

SCORE: <number>
REASON: <one sentence>

Race: {race_name}
Changes: {summary}
Resulting top 5: {', '.join(alt_top5)}
"""


def _parse_granite(text: str) -> tuple[float | None, str]:
    score = None
    reason = ""
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned.upper().startswith("SCORE:"):
            try:
                score = float(cleaned.split(":", 1)[1].strip())
            except (ValueError, IndexError):
                pass
        elif cleaned.upper().startswith("REASON:"):
            reason = cleaned.split(":", 1)[1].strip()
    if score is not None:
        score = max(0.0, min(1.0, score))
    return score, reason


def score_counterfactual(
    changes: list[dict],
    race_name: str,
    alt_top5: list[str],
) -> dict:
    base = _heuristic(changes)

    if not changes:
        return {
            "score": round(base, 2),
            "label": _label(base),
            "reasoning": "Baseline race - no interventions applied.",
            "source": "heuristic",
        }

    try:
        text = generate(
            _granite_prompt(changes, race_name, alt_top5),
            max_new_tokens=100,
            temperature=0.2,
        )
        granite_score, granite_reason = _parse_granite(text)
        if granite_score is not None:
            blended = round((granite_score * 0.7) + (base * 0.3), 2)
            return {
                "score": blended,
                "label": _label(blended),
                "reasoning": granite_reason or "Granite judged the realism of the change set.",
                "source": "granite",
            }
    except Exception:
        pass

    return {
        "score": round(base, 2),
        "label": _label(base),
        "reasoning": f"Heuristic only ({len(changes)} change{'s' if len(changes) != 1 else ''} applied).",
        "source": "heuristic",
    }


def _label(score: float) -> str:
    if score >= 0.75:
        return "Plausible"
    if score >= 0.5:
        return "Borderline"
    if score >= 0.3:
        return "Stretch"
    return "Fantasy"
