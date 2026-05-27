"""Pure-function tests for ai.forecast - no DB required."""

from ai import forecast


def test_default_dna_has_all_keys():
    for key in ("overtaking", "tire_deg", "safety_car_prob", "weather_risk"):
        assert key in forecast.DEFAULT_DNA
        assert 0.0 <= forecast.DEFAULT_DNA[key] <= 1.0


def test_suggest_strategy_top_runners_protect_track_position():
    assert "Track-position" in forecast._suggest_strategy(1)
    assert "Track-position" in forecast._suggest_strategy(3)


def test_suggest_strategy_midfield_recommends_one_stop():
    out = forecast._suggest_strategy(6)
    assert "1-stop" in out


def test_suggest_strategy_backmarkers_gamble_on_safety_car():
    out = forecast._suggest_strategy(18)
    assert "safety car" in out.lower()


def test_risk_factors_default_dna_is_balanced():
    risks = forecast._risk_factors(dict(forecast.DEFAULT_DNA))
    assert risks == ["Balanced circuit - free strategic choice"]


def test_risk_factors_high_safety_car_flagged():
    dna = {**forecast.DEFAULT_DNA, "safety_car_prob": 0.9}
    risks = forecast._risk_factors(dna)
    assert any("safety car" in r.lower() for r in risks)


def test_risk_factors_high_tire_deg_flagged():
    dna = {**forecast.DEFAULT_DNA, "tire_deg": 0.8}
    risks = forecast._risk_factors(dna)
    assert any("tire" in r.lower() for r in risks)


def test_risk_factors_low_overtaking_flagged():
    dna = {**forecast.DEFAULT_DNA, "overtaking": 0.1}
    risks = forecast._risk_factors(dna)
    assert any("overtaking" in r.lower() for r in risks)


def test_risk_factors_weather_variability_flagged():
    dna = {**forecast.DEFAULT_DNA, "weather_risk": 0.7}
    risks = forecast._risk_factors(dna)
    assert any("weather" in r.lower() for r in risks)


def test_risk_factors_aggregates_multiple_warnings():
    dna = {
        "overtaking": 0.1,
        "tire_deg": 0.9,
        "safety_car_prob": 0.8,
        "weather_risk": 0.6,
    }
    risks = forecast._risk_factors(dna)
    # All four risks active -> none of the warnings should be missing
    assert len(risks) >= 4


def test_circuit_dna_returns_default_when_circuit_id_missing():
    out = forecast._circuit_dna(db=None, circuit_id=None)
    assert out == forecast.DEFAULT_DNA


def test_build_forecast_returns_shape_when_race_missing(monkeypatch):
    """No race -> safe defaults, no crash."""

    class _StubSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, model, _id):
            return None

    monkeypatch.setattr(forecast, "SessionLocal", _StubSession)
    out = forecast.build_forecast(99_999_999)
    assert out["race_id"] == 99_999_999
    assert out["predictions"] == []
    assert "Race not found" in out["risk_factors"]
