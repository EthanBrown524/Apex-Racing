"""Shared utilities for counterfactual change descriptions and value coercion.

Used by ai.counterfactual (apply changes), ai.glory_path (narrate applied
interventions), and the API layer (response summaries).
"""

from __future__ import annotations


MECHANICAL_PENALTY_MS = 800
WEATHER_PENALTY_MS = 1200
SC_PIT_SAVINGS_MS = 12000
GRID_DELTA_MS = 350


def safe_int(value) -> int | None:
    """Coerce a value to int or return None - never raise."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def describe_change(c: dict) -> str:
    """Human-readable one-liner for a counterfactual change.
    Shared between the simulation summary and Glory Path narration."""
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


def strip_internal(change: dict) -> dict:
    """Drop keys that start with underscore - used by Glory Path to surface
    the rationale fields privately while keeping the change payload clean."""
    return {k: v for k, v in change.items() if not k.startswith("_")}
