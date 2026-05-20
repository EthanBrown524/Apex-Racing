"""Curated demo scenarios - one-click loadable from the Showcase page.

Each scenario references a race by (season, round) so the frontend can resolve
to a race_id at runtime regardless of ingestion order. The scenarios mix
counterfactual + Glory Path demos so a judge gets to see both modes without
needing to know F1 driver codes.
"""

from __future__ import annotations


SHOWCASE_SCENARIOS = [
    {
        "id": "abu-dhabi-2021",
        "title": "Abu Dhabi 2021 - the title-deciding lap",
        "subtitle": "Don't restart the race behind the safety car. Who wins the championship?",
        "season": 2021,
        "round": 22,
        "mode": "counterfactual",
        "changes": [
            {"driver_code": "VER", "change_type": "mechanical", "lap": 53, "value": 1500},
        ],
        "tagline": "Hamilton vs Verstappen",
        "accent": "#e8002d",
    },
    {
        "id": "monaco-2022",
        "title": "Monaco 2022 - if Ferrari hadn't double-stacked",
        "subtitle": "Move LEC's pit stop two laps earlier; does he keep the win at home?",
        "season": 2022,
        "round": 7,
        "mode": "counterfactual",
        "changes": [
            {"driver_code": "LEC", "change_type": "pit_lap", "lap": 22, "value": 18},
        ],
        "tagline": "Charles's home cathedral",
        "accent": "#dc0000",
    },
    {
        "id": "brazil-2022",
        "title": "Brazil 2022 - Russell's maiden victory",
        "subtitle": "What if the safety car at lap 7 had stayed deployed two laps longer?",
        "season": 2022,
        "round": 21,
        "mode": "counterfactual",
        "changes": [
            {"driver_code": "", "change_type": "safety_car", "lap": 7, "value": 7},
        ],
        "tagline": "George's first",
        "accent": "#00d2be",
    },
    {
        "id": "singapore-2023",
        "title": "Singapore 2023 - what if it rained?",
        "subtitle": "Weather window from lap 25 onward. Who benefits?",
        "season": 2023,
        "round": 16,
        "mode": "counterfactual",
        "changes": [
            {"driver_code": "", "change_type": "weather", "lap": 25,
             "value": {"benefits": ["VER", "PER"], "penalty_ms": 1500}},
        ],
        "tagline": "Marina Bay in the wet",
        "accent": "#4cc9f0",
    },
    {
        "id": "glory-alonso",
        "title": "Glory Path - Alonso back to the top step",
        "subtitle": "Pick any 2023 race - APEX finds the smallest set of changes for ALO to win.",
        "season": 2023,
        "round": 7,
        "mode": "glory_path",
        "driver_code": "ALO",
        "target_position": 1,
        "tagline": "El Plan, alternate timeline",
        "accent": "#006f62",
    },
    {
        "id": "glory-leclerc",
        "title": "Glory Path - Leclerc's lost Monaco",
        "subtitle": "Solve a P1 finish at Monaco 2022.",
        "season": 2022,
        "round": 7,
        "mode": "glory_path",
        "driver_code": "LEC",
        "target_position": 1,
        "tagline": "The home jinx, lifted",
        "accent": "#dc0000",
    },
]


def list_scenarios() -> list[dict]:
    return [
        {k: v for k, v in scenario.items()}
        for scenario in SHOWCASE_SCENARIOS
    ]


def get_scenario(scenario_id: str) -> dict | None:
    for scenario in SHOWCASE_SCENARIOS:
        if scenario["id"] == scenario_id:
            return dict(scenario)
    return None
