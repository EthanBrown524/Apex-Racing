from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai.commentary import answer_question, narrate_race
from db.connection import get_db
from db.models import Race


router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    race_id: int
    question: str = Field(min_length=1, max_length=500)


@router.get("/commentary/{race_id}")
def commentary(
    race_id: int,
    up_to_lap: int | None = Query(default=None, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    if db.get(Race, race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return narrate_race(race_id, up_to_lap=up_to_lap)


@router.post("/ask")
def ask(payload: AskRequest, db: Session = Depends(get_db)) -> dict:
    if db.get(Race, payload.race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return answer_question(payload.race_id, payload.question)
