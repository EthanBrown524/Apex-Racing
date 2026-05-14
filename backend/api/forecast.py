from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai.forecast import build_forecast
from db.connection import get_db
from db.models import Race


router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/{race_id}")
def forecast_race(race_id: int, db: Session = Depends(get_db)) -> dict:
    if db.get(Race, race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")

    return build_forecast(race_id)
