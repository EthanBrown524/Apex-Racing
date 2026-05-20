"""Realism scoring tests - exercises the heuristic without calling Granite."""

import os
import pytest

from ai import realism


@pytest.fixture(autouse=True)
def _no_granite(monkeypatch):
    """Force Granite to be unavailable so the heuristic path runs."""
    monkeypatch.delenv("IBM_API_KEY", raising=False)
    monkeypatch.delenv("WATSONX_PROJECT_ID", raising=False)


def test_no_changes_is_perfectly_realistic():
    out = realism.score_counterfactual([], race_name="Test GP", alt_top5=[])
    assert out["score"] == 1.0
    assert out["label"] == "Plausible"


def test_one_change_remains_plausible():
    out = realism.score_counterfactual(
        [{"change_type": "pit_lap", "driver_code": "HAM", "lap": 14, "value": 18}],
        race_name="Test GP",
        alt_top5=["HAM", "VER"],
    )
    assert 0.8 <= out["score"] <= 1.0
    assert out["label"] == "Plausible"


def test_many_aggressive_changes_drop_into_fantasy():
    huge = [
        {"change_type": "weather", "lap": 1, "value": {"benefits": ["HAM"]}},
        {"change_type": "safety_car", "lap": 5, "value": 5},
        {"change_type": "dnf", "driver_code": "VER", "lap": 1},
        {"change_type": "dnf", "driver_code": "PER", "lap": 2},
        {"change_type": "dnf", "driver_code": "LEC", "lap": 3},
        {"change_type": "mechanical", "driver_code": "SAI", "lap": 4, "value": 5000},
    ]
    out = realism.score_counterfactual(huge, race_name="Test GP", alt_top5=["HAM"])
    assert out["score"] < 0.5
    assert out["label"] in {"Stretch", "Fantasy", "Borderline"}


def test_score_is_clamped():
    out = realism.score_counterfactual([], race_name="X", alt_top5=[])
    assert 0.0 <= out["score"] <= 1.0
