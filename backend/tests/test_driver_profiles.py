"""Test the driver profile helpers that don't need a DB."""

from ai import driver_profiles as dp


def test_default_profile_has_all_keys():
    for key in ("wet_skill", "tyre_management", "aggression", "consistency", "race_pace_index"):
        assert key in dp.DEFAULT_PROFILE


def test_clamp_keeps_value_in_range():
    assert dp._clamp01(0.0) == 0.0
    assert dp._clamp01(1.0) == 1.0
    assert dp._clamp01(-0.5) == 0.0
    assert dp._clamp01(2.0) == 1.0
    assert dp._clamp01(0.5) == 0.5


def test_summarize_profile_line_includes_every_axis():
    profile = {
        "code": "VER",
        "wet_skill": 0.85,
        "tyre_management": 0.92,
        "aggression": 0.78,
        "consistency": 0.88,
        "race_pace_index": 1.4,
    }
    line = dp.summarize_profile_line(profile)
    assert "VER" in line
    assert "0.85" in line
    assert "0.92" in line
    assert "1.4" in line


def test_summarize_profile_uses_defaults_when_keys_missing():
    line = dp.summarize_profile_line({"code": "???"})
    assert "0.5" in line
    assert "???" in line


def test_build_profiles_for_race_returns_empty_on_missing_race(monkeypatch):
    from ai import driver_profiles

    class _SessionStub:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, model, _id):
            return None

    monkeypatch.setattr(driver_profiles, "SessionLocal", _SessionStub)
    out = driver_profiles.build_profiles_for_race(99_999_999)
    assert out == {}
