"""Test the Race Director -> change record translator."""

from ai import change_expander as ex


def test_pit_action_emits_pit_lap_change():
    out = ex.expand_decision({"driver_code": "VER", "action": "pit", "lap": 26})
    assert out is not None
    assert out["change_type"] == "pit_lap"
    assert out["driver_code"] == "VER"
    assert out["value"] == 26


def test_retire_action_emits_dnf_change():
    out = ex.expand_decision({"driver_code": "PER", "action": "retire", "lap": 32})
    assert out is not None
    assert out["change_type"] == "dnf"
    assert out["lap"] == 32


def test_push_action_emits_fastest_lap_below_baseline():
    out = ex.expand_decision(
        {"driver_code": "LEC", "action": "push", "lap": 18}, baseline_lap_ms=85_000
    )
    assert out is not None
    assert out["change_type"] == "fastest_lap"
    assert out["value"] == 85_000 + ex.PUSH_DELTA_MS


def test_push_action_falls_back_when_no_baseline():
    out = ex.expand_decision({"driver_code": "LEC", "action": "push", "lap": 18})
    assert out is not None
    assert out["value"] == ex.FALLBACK_LAP_TIME_MS + ex.PUSH_DELTA_MS


def test_manage_action_emits_mechanical_penalty():
    out = ex.expand_decision({"driver_code": "ALO", "action": "manage", "lap": 12})
    assert out is not None
    assert out["change_type"] == "mechanical"
    assert out["value"] == ex.MANAGE_PENALTY_MS


def test_stay_out_returns_none():
    out = ex.expand_decision({"driver_code": "HAM", "action": "stay_out", "lap": 25})
    assert out is None


def test_unknown_action_returns_none():
    out = ex.expand_decision({"driver_code": "HAM", "action": "snooze", "lap": 25})
    assert out is None


def test_missing_driver_returns_none():
    out = ex.expand_decision({"action": "pit", "lap": 25})
    assert out is None


def test_missing_lap_returns_none():
    out = ex.expand_decision({"driver_code": "HAM", "action": "pit"})
    assert out is None


def test_expand_plan_attaches_metadata():
    plan = {
        "decisions": [
            {
                "driver_code": "VER",
                "action": "pit",
                "lap": 26,
                "confidence": 0.8,
                "rationale": "cover the leader",
            }
        ]
    }
    out = ex.expand_plan(plan)
    assert len(out) == 1
    change = out[0]
    assert change["_origin"] == "race_director"
    assert change["_rationale"] == "cover the leader"
    assert change["_confidence"] == 0.8
    assert change["_action"] == "pit"


def test_expand_plans_aggregates_multiple():
    plans = [
        {"decisions": [{"driver_code": "VER", "action": "pit", "lap": 26}]},
        {"decisions": [{"driver_code": "HAM", "action": "stay_out", "lap": 25}]},
        {"decisions": [{"driver_code": "STR", "action": "retire", "lap": 28}]},
    ]
    out = ex.expand_plans(plans)
    assert len(out) == 2
    actions = {c["change_type"] for c in out}
    assert actions == {"pit_lap", "dnf"}


def test_expand_plan_uses_baseline_per_driver():
    plan = {"decisions": [{"driver_code": "LEC", "action": "push", "lap": 18}]}
    out = ex.expand_plan(plan, baseline_laps_by_code={"LEC": 84_000})
    assert out[0]["value"] == 84_000 + ex.PUSH_DELTA_MS
