"""Pure-function tests for ai.championship.

The end-to-end `compute_championship_impact` is DB-heavy; here we exercise
the deterministic helpers (points table, ranking, narration, alternate
points synthesis from a final-lap snapshot).
"""

from ai import championship


def test_points_table_matches_f1_standard():
    assert championship.POINTS_TABLE == [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def test_points_for_position_p1_through_p10():
    assert championship._points_for_position(1) == 25.0
    assert championship._points_for_position(2) == 18.0
    assert championship._points_for_position(10) == 1.0


def test_points_for_position_outside_top_ten_is_zero():
    assert championship._points_for_position(11) == 0.0
    assert championship._points_for_position(20) == 0.0


def test_points_for_position_handles_none_and_invalid():
    assert championship._points_for_position(None) == 0.0
    assert championship._points_for_position(0) == 0.0
    assert championship._points_for_position(-1) == 0.0


def test_alternate_points_from_final_lap_snapshot():
    alt_laps = [
        {
            "lap": 50,
            "drivers": [
                {"code": "HAM", "position": 1},
                {"code": "VER", "position": 2},
                {"code": "LEC", "position": 11},
            ],
        }
    ]
    code_to_driver_id = {"HAM": 1, "VER": 2, "LEC": 3}
    out = championship._alternate_points_per_driver(alt_laps, code_to_driver_id)
    assert out[1] == 25.0
    assert out[2] == 18.0
    assert out[3] == 0.0


def test_alternate_points_ignores_unknown_codes():
    alt_laps = [
        {"lap": 1, "drivers": [{"code": "GHOST", "position": 1}]}
    ]
    code_to_driver_id = {"HAM": 1}
    assert championship._alternate_points_per_driver(alt_laps, code_to_driver_id) == {}


def test_alternate_points_empty_when_no_laps():
    assert championship._alternate_points_per_driver([], {"HAM": 1}) == {}


def test_alternate_points_uses_only_final_lap():
    alt_laps = [
        {"lap": 1, "drivers": [{"code": "VER", "position": 1}]},
        {"lap": 50, "drivers": [{"code": "HAM", "position": 1}]},
    ]
    out = championship._alternate_points_per_driver(alt_laps, {"HAM": 1, "VER": 2})
    assert out.get(1) == 25.0
    assert 2 not in out  # VER's lap-1 lead is irrelevant


def test_rank_orders_by_points_descending():
    rows = [
        {"code": "PER", "points": 200.0},
        {"code": "HAM", "points": 400.0},
        {"code": "VER", "points": 575.0},
    ]
    ranked = championship._rank(rows)
    assert [r["code"] for r in ranked] == ["VER", "HAM", "PER"]


def test_rank_returns_list_for_empty_input():
    assert championship._rank([]) == []


def test_narrative_when_champion_unchanged():
    out = championship._narrative(
        season=2023,
        race_name="Bahrain GP",
        actual_top3=[],
        alt_top3=[],
        actual_champion="VER",
        alt_champion="VER",
        delta_summary=["HAM +3pts"],
    )
    assert "VER" in out
    assert "Bahrain GP" in out
    assert "stays put" in out


def test_narrative_when_title_flips():
    out = championship._narrative(
        season=2021,
        race_name="Abu Dhabi GP",
        actual_top3=[],
        alt_top3=[],
        actual_champion="VER",
        alt_champion="HAM",
        delta_summary=["VER -25pts", "HAM +7pts"],
    )
    assert "HAM" in out
    assert "VER" in out
    assert "Abu Dhabi GP" in out
    assert "2021" in out
