from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai.counterfactual import simulate_counterfactual


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
def simulate(payload: CounterfactualRequest) -> dict:
    return simulate_counterfactual(
        race_id=payload.race_id,
        changes=[change.model_dump() for change in payload.changes],
    )

