def simulate_counterfactual(race_id: int, changes: list[dict]) -> dict:
    """Initial deterministic placeholder until the race model is trained."""
    return {
        "race_id": race_id,
        "alt_laps": [],
        "explanation": (
            "Counterfactual simulation scaffolding is ready. "
            "Next step: load baseline lap data, apply strategy deltas, and ask Granite for narrative context."
        ),
        "changes": changes,
    }

