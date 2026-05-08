from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Race, Scenario


router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    race_id: int
    changes: list[dict] = Field(default_factory=list)


@router.post("")
def create_scenario(payload: ScenarioCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(Race, payload.race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")

    scenario = Scenario(label=payload.label, race_id=payload.race_id, changes=payload.changes)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return {"scenario_id": str(scenario.id)}


@router.get("")
def list_scenarios(db: Session = Depends(get_db)) -> list[dict]:
    scenarios = db.execute(select(Scenario).order_by(Scenario.created_at.desc())).scalars()
    return [
        {
            "scenario_id": str(scenario.id),
            "label": scenario.label,
            "race_id": scenario.race_id,
            "changes": scenario.changes,
            "created_at": scenario.created_at.isoformat(),
        }
        for scenario in scenarios
    ]

