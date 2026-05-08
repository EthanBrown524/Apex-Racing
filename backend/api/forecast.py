from fastapi import APIRouter

from ai.forecast import build_forecast


router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/{race_id}")
def forecast_race(race_id: int) -> dict:
    return build_forecast(race_id)

