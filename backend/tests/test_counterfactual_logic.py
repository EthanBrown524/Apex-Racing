"""Test the counterfactual engine's pure-logic pieces (no DB).

We invoke the internal _recompute_positions and _apply_changes against a
hand-built fake baseline rather than spinning up Postgres.
"""

from ai import counterfactual as cf


def _baseline():
    """Two drivers, three laps. HAM leads VER by exactly 1s every lap."""
    return {
        "race": type("Race", (), {"name": "Test GP", "total_laps": 3})(),
        "drivers_by_id": {1: "HAM", 2: "VER"},
        "laps_by_driver": {
            1: [
                {"lap": 1, "time_ms": 90000, "position": 1, "gap_ms": 0, "in_pit": False, "pit_duration_ms": None},
                {"lap": 2, "time_ms": 90000, "position": 1, "gap_ms": 0, "in_pit": False, "pit_duration_ms": None},
                {"lap": 3, "time_ms": 90000, "position": 1, "gap_ms": 0, "in_pit": False, "pit_duration_ms": None},
            ],
            2: [
                {"lap": 1, "time_ms": 91000, "position": 2, "gap_ms": 1000, "in_pit": False, "pit_duration_ms": None},
                {"lap": 2, "time_ms": 91000, "position": 2, "gap_ms": 1000, "in_pit": False, "pit_duration_ms": None},
                {"lap": 3, "time_ms": 91000, "position": 2, "gap_ms": 1000, "in_pit": False, "pit_duration_ms": None},
            ],
        },
        "pit_lookup": {},
        "safety_cars": [],
    }


def test_no_changes_preserves_leader():
    baseline = _baseline()
    laps = cf._apply_changes(baseline, [])
    alt = cf._recompute_positions(laps, baseline["drivers_by_id"], total_laps=3)
    assert alt[-1]["drivers"][0]["code"] == "HAM"
    assert alt[-1]["drivers"][1]["code"] == "VER"


def test_dnf_drops_driver_after_lap():
    baseline = _baseline()
    laps = cf._apply_changes(
        baseline,
        [{"driver_code": "HAM", "change_type": "dnf", "lap": 2}],
    )
    assert len(laps[1]) == 1
    assert laps[1][0]["lap"] == 1

    alt = cf._recompute_positions(laps, baseline["drivers_by_id"], total_laps=3)
    final = alt[-1]
    assert final["drivers"][0]["code"] == "VER"


def test_mechanical_adds_recurring_penalty():
    baseline = _baseline()
    laps = cf._apply_changes(
        baseline,
        [{"driver_code": "HAM", "change_type": "mechanical", "lap": 2, "value": 2000}],
    )
    hams_laps = laps[1]
    assert hams_laps[0]["time_ms"] == 90000
    assert hams_laps[1]["time_ms"] == 92000
    assert hams_laps[2]["time_ms"] == 92000


def test_fastest_lap_rewrites_single_lap():
    baseline = _baseline()
    laps = cf._apply_changes(
        baseline,
        [{"driver_code": "VER", "change_type": "fastest_lap", "lap": 2, "value": 70000}],
    )
    vers_laps = laps[2]
    assert vers_laps[0]["time_ms"] == 91000
    assert vers_laps[1]["time_ms"] == 70000
    assert vers_laps[2]["time_ms"] == 91000


def test_recompute_positions_handles_uneven_laps():
    """A driver retiring should not break the rank calculation for survivors."""
    baseline = _baseline()
    laps = cf._apply_changes(
        baseline,
        [{"driver_code": "HAM", "change_type": "dnf", "lap": 2}],
    )
    alt = cf._recompute_positions(laps, baseline["drivers_by_id"], total_laps=3)
    assert len(alt) == 3
    assert alt[0]["drivers"][0]["code"] == "HAM"
    assert alt[1]["drivers"][0]["code"] == "VER"
    assert alt[2]["drivers"][0]["code"] == "VER"
