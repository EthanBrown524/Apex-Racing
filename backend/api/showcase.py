from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ai.showcase_scenarios import get_scenario, list_scenarios
from db.connection import SessionLocal
from db.models import Race


router = APIRouter(prefix="/showcase", tags=["showcase"])


def _resolve_race_id(season: int, round_number: int) -> int | None:
    with SessionLocal() as db:
        row = db.execute(
            select(Race.id).where(
                Race.season_year == season, Race.round == round_number
            )
        ).first()
        return row[0] if row else None


@router.get("")
def list_demo_scenarios() -> list[dict]:
    enriched = []
    for scenario in list_scenarios():
        race_id = _resolve_race_id(scenario["season"], scenario["round"])
        enriched.append({**scenario, "race_id": race_id})
    return enriched


@router.get("/{scenario_id}")
def get_demo_scenario(scenario_id: str) -> dict:
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario["race_id"] = _resolve_race_id(scenario["season"], scenario["round"])
    return scenario
