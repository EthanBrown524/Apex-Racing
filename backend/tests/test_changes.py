"""Pure-function tests for the shared change helpers - no DB required."""

from ai.changes import (
    MECHANICAL_PENALTY_MS,
    describe_change,
    safe_int,
    strip_internal,
)


def test_safe_int_handles_none_and_garbage():
    assert safe_int(None) is None
    assert safe_int("abc") is None
    assert safe_int("12") == 12
    assert safe_int(12.7) == 12
    assert safe_int(True) == 1


def test_describe_change_covers_every_change_type():
    cases = [
        {"change_type": "pit_lap", "driver_code": "HAM", "lap": 20, "value": 14},
        {"change_type": "dnf", "driver_code": "VER", "lap": 32},
        {"change_type": "fastest_lap", "driver_code": "LEC", "lap": 18, "value": 84000},
        {"change_type": "mechanical", "driver_code": "RUS", "lap": 5, "value": 1200},
        {"change_type": "weather", "lap": 25, "value": {"benefits": ["VER", "HAM"]}},
        {"change_type": "safety_car", "lap": 10, "value": 10},
        {"change_type": "grid_swap", "driver_code": "ALO", "value": "STR"},
    ]
    for change in cases:
        out = describe_change(change)
        assert isinstance(out, str) and out
        if "driver_code" in change and change["driver_code"]:
            assert change["driver_code"] in out


def test_describe_mechanical_uses_default_penalty_when_value_missing():
    out = describe_change(
        {"change_type": "mechanical", "driver_code": "PER", "lap": 30}
    )
    assert "PER" in out
    assert str(MECHANICAL_PENALTY_MS) in out


def test_describe_weather_handles_missing_value():
    out = describe_change({"change_type": "weather", "lap": 25})
    assert "25" in out
    assert "none" in out


def test_describe_safety_car_prefers_value_over_lap():
    out = describe_change({"change_type": "safety_car", "lap": 5, "value": 12})
    assert "12" in out


def test_describe_unknown_change_type_does_not_crash():
    out = describe_change(
        {"driver_code": "BOT", "change_type": "teleport", "lap": 1}
    )
    assert "BOT" in out
    assert "teleport" in out


def test_strip_internal_keeps_normal_keys_intact():
    original = {"a": 1, "b": 2, "c": 3}
    assert strip_internal(original) == original


def test_strip_internal_removes_underscore_keys():
    raw = {
        "driver_code": "HAM",
        "change_type": "pit_lap",
        "lap": 14,
        "value": 18,
        "_reason": "internal",
        "_expected_gain": 2,
    }
    cleaned = strip_internal(raw)
    assert "_reason" not in cleaned
    assert "_expected_gain" not in cleaned
    assert cleaned["driver_code"] == "HAM"
    assert cleaned["lap"] == 14
