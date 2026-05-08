def build_forecast(race_id: int) -> dict:
    """Initial forecast shape for frontend integration."""
    return {
        "race_id": race_id,
        "predictions": [],
        "circuit_dna": {
            "overtaking": 0.0,
            "tire_deg": 0.0,
            "safety_car_prob": 0.0,
            "weather_risk": 0.0,
        },
        "risk_factors": [],
    }

