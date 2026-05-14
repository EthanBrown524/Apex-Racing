from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai.counterfactual import simulate_counterfactual
from db.connection import get_db
from db.models import Race


router = APIRouter(prefix="/counterfactual", tags=["counterfactual"])


class CounterfactualChange(BaseModel):
    driver_code: str
    change_type: str
    lap: int | None = None
    value: str | int | float | bool | None = None


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
