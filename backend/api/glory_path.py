from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai.glory_path import find_glory_path
from db.connection import get_db
from db.models import Race


router = APIRouter(prefix="/glory-path", tags=["glory-path"])


class GloryPathRequest(BaseModel):
    race_id: int
    driver_code: str = Field(min_length=1, max_length=4)
    target_position: int = Field(default=1, ge=1, le=20)


@router.post("/solve")
def solve(payload: GloryPathRequest, db: Session = Depends(get_db)) -> dict:
    if db.get(Race, payload.race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return find_glory_path(
        race_id=payload.race_id,
        driver_code=payload.driver_code,
        target_position=payload.target_position,
    )
