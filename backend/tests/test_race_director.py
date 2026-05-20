"""Test the Race Director module's pure-logic pieces.

JSON extraction, schema validation, and trigger detection are all tested
without calling Granite or hitting the database.
"""

import pytest

from ai import race_director as rd


def test_extract_json_handles_clean_json():
    raw = '{"decisions": [{"driver_code": "VER", "action": "pit", "lap": 26}]}'
    parsed = rd._extract_json(raw)
    assert parsed is not None
    assert parsed["decisions"][0]["driver_code"] == "VER"


def test_extract_json_strips_preamble_and_codefence():
    raw = """Sure! Here's the plan:
```json
{"decisions": [{"driver_code": "HAM", "action": "stay_out", "lap": 25}]}
```
Hope this helps."""
    parsed = rd._extract_json(raw)
    assert parsed is not None
    assert parsed["decisions"][0]["action"] == "stay_out"


def test_extract_json_returns_none_on_garbage():
    assert rd._extract_json("not json at all") is None
    assert rd._extract_json("") is None
    assert rd._extract_json(None) is None
    assert rd._extract_json("{unclosed: brace") is None


def test_validate_plan_drops_unknown_drivers():
    profiles = {"VER": {"code": "VER"}, "HAM": {"code": "HAM"}}
    raw = {
        "decisions": [
            {"driver_code": "VER", "action": "pit", "lap": 26, "confidence": 0.8, "rationale": "ok"},
            {"driver_code": "XXX", "action": "pit", "lap": 26, "confidence": 0.8, "rationale": "bad"},
        ]
    }
    out = rd._validate_plan(raw, profiles)
    assert len(out["decisions"]) == 1
    assert out["decisions"][0]["driver_code"] == "VER"


def test_validate_plan_drops_unknown_actions():
    profiles = {"VER": {"code": "VER"}}
    raw = {
        "decisions": [
            {"driver_code": "VER", "action": "explode", "lap": 26},
            {"driver_code": "VER", "action": "PIT", "lap": 26},
        ]
    }
    out = rd._validate_plan(raw, profiles)
    assert len(out["decisions"]) == 1
    assert out["decisions"][0]["action"] == "pit"


def test_validate_plan_clamps_confidence_and_lap():
    profiles = {"VER": {"code": "VER"}}
    raw = {
        "decisions": [
            {"driver_code": "VER", "action": "pit", "lap": -5, "confidence": 2.0},
        ]
    }
    out = rd._validate_plan(raw, profiles)
    assert out["decisions"][0]["lap"] == 1
    assert out["decisions"][0]["confidence"] == 1.0


def test_validate_plan_caps_decision_count():
    profiles = {f"D{i:02d}": {"code": f"D{i:02d}"} for i in range(20)}
    raw = {
        "decisions": [
            {"driver_code": f"D{i:02d}", "action": "pit", "lap": 1}
            for i in range(20)
        ]
    }
    out = rd._validate_plan(raw, profiles)
    assert len(out["decisions"]) <= rd.MAX_DECISIONS


def test_validate_plan_handles_missing_decisions_key():
    out = rd._validate_plan({}, {})
    assert out["decisions"] == []


def test_validate_plan_handles_non_dict():
    out = rd._validate_plan("not a dict", {})
    assert out["decisions"] == []


def test_is_strategic_trigger():
    assert rd._is_strategic_trigger({"change_type": "weather"})
    assert rd._is_strategic_trigger({"change_type": "safety_car"})
    assert rd._is_strategic_trigger({"change_type": "mechanical"})
    assert rd._is_strategic_trigger({"change_type": "dnf"})
    assert not rd._is_strategic_trigger({"change_type": "pit_lap"})
    assert not rd._is_strategic_trigger({"change_type": "fastest_lap"})
    assert not rd._is_strategic_trigger({"change_type": "grid_swap"})


def test_trigger_summary_per_type():
    assert "lap 25" in rd._trigger_summary(
        {"change_type": "weather", "lap": 25, "value": {"benefits": ["HAM"]}}
    )
    assert "Safety car" in rd._trigger_summary(
        {"change_type": "safety_car", "lap": 10, "value": 10}
    )
    assert "VER" in rd._trigger_summary(
        {"change_type": "dnf", "driver_code": "VER", "lap": 20}
    )
    assert rd._trigger_summary({"change_type": "pit_lap"}) == ""


def test_plan_response_returns_empty_on_no_profiles(monkeypatch):
    monkeypatch.setattr(rd, "build_profiles_for_race", lambda race_id: {})
    out = rd.plan_response(race_id=1, race_name="X", trigger={"change_type": "weather", "lap": 1})
    assert out["decisions"] == []


def test_plan_response_returns_empty_on_non_strategic(monkeypatch):
    monkeypatch.setattr(
        rd,
        "build_profiles_for_race",
        lambda race_id: {"VER": {"code": "VER"}},
    )
    out = rd.plan_response(
        race_id=1, race_name="X", trigger={"change_type": "pit_lap", "lap": 1}
    )
    assert out["decisions"] == []
