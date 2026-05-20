"""Tests for the curated showcase scenarios - no DB needed."""

from ai.showcase_scenarios import SHOWCASE_SCENARIOS, get_scenario, list_scenarios


REQUIRED_KEYS = {"id", "title", "subtitle", "season", "round", "mode", "tagline"}
VALID_MODES = {"counterfactual", "glory_path"}


def test_scenarios_have_unique_ids():
    ids = [s["id"] for s in SHOWCASE_SCENARIOS]
    assert len(ids) == len(set(ids))


def test_every_scenario_has_required_keys():
    for scenario in SHOWCASE_SCENARIOS:
        missing = REQUIRED_KEYS - scenario.keys()
        assert not missing, f"{scenario['id']} is missing {missing}"
        assert scenario["mode"] in VALID_MODES
        assert isinstance(scenario["season"], int)
        assert isinstance(scenario["round"], int)


def test_counterfactual_scenarios_have_changes():
    for scenario in SHOWCASE_SCENARIOS:
        if scenario["mode"] == "counterfactual":
            assert "changes" in scenario
            assert isinstance(scenario["changes"], list)
            assert scenario["changes"], f"{scenario['id']} has no changes"


def test_glory_path_scenarios_have_target():
    for scenario in SHOWCASE_SCENARIOS:
        if scenario["mode"] == "glory_path":
            assert scenario.get("driver_code"), f"{scenario['id']} missing driver_code"
            assert 1 <= scenario.get("target_position", 0) <= 20


def test_get_scenario_resolves_existing():
    first = SHOWCASE_SCENARIOS[0]
    assert get_scenario(first["id"]) is not None
    assert get_scenario("does-not-exist") is None


def test_list_scenarios_returns_copies():
    scenarios = list_scenarios()
    scenarios[0]["title"] = "MUTATED"
    assert SHOWCASE_SCENARIOS[0]["title"] != "MUTATED"
