from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai.championship import compute_championship_impact
from db.connection import get_db
from db.models import Race


router = APIRouter(prefix="/championship", tags=["championship"])


class ChampionshipImpactRequest(BaseModel):
    race_id: int
    changes: list[dict] = Field(default_factory=list)


@router.post("/impact")
def impact(payload: ChampionshipImpactRequest, db: Session = Depends(get_db)) -> dict:
    if db.get(Race, payload.race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return compute_championship_impact(payload.race_id, payload.changes)
