from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai.counterfactual import simulate_counterfactual
from ai.realism import score_counterfactual
from db.connection import get_db
from db.models import Race


router = APIRouter(prefix="/counterfactual", tags=["counterfactual"])


class CounterfactualChange(BaseModel):
    driver_code: str = ""
    change_type: str
    lap: int | None = None
    value: str | int | float | bool | dict | list | None = None


class CounterfactualRequest(BaseModel):
    race_id: int
    changes: list[CounterfactualChange] = Field(default_factory=list)


@router.post("/simulate")
def simulate(payload: CounterfactualRequest, db: Session = Depends(get_db)) -> dict:
    if db.get(Race, payload.race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")

    return simulate_counterfactual(
        race_id=payload.race_id,
        changes=[change.model_dump() for change in payload.changes],
    )


@router.post("/realism")
def realism(payload: CounterfactualRequest, db: Session = Depends(get_db)) -> dict:
    """Realism score for a counterfactual. Called in parallel with /simulate
    by the frontend so the Granite judgement doesn't block the leaderboard."""
    race = db.get(Race, payload.race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="Race not found")

    changes = [c.model_dump() for c in payload.changes]

    simulated = simulate_counterfactual(payload.race_id, changes)
    return score_counterfactual(
        changes=changes,
        race_name=race.name or f"Race {payload.race_id}",
        alt_top5=simulated.get("alt_top5", []),
    )
