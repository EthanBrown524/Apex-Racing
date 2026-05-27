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
    ai_director: bool = False


@router.post("/simulate")
def simulate(payload: CounterfactualRequest, db: Session = Depends(get_db)) -> dict:
    if db.get(Race, payload.race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")

    return simulate_counterfactual(
        race_id=payload.race_id,
        changes=[change.model_dump() for change in payload.changes],
        ai_director=payload.ai_director,
    )


class CompareRequest(BaseModel):
    race_id: int
    scenario_a: list[CounterfactualChange] = Field(default_factory=list)
    scenario_b: list[CounterfactualChange] = Field(default_factory=list)
    label_a: str = "A"
    label_b: str = "B"


def _final_positions(alt_laps: list[dict]) -> dict[str, int]:
    if not alt_laps:
        return {}
    final = alt_laps[-1]
    return {d["code"]: d["position"] for d in final.get("drivers", [])}


@router.post("/compare")
def compare(payload: CompareRequest, db: Session = Depends(get_db)) -> dict:
    """Run two counterfactual scenarios against the same race and return a
    final-lap position diff per driver. Each scenario reuses the standard
    simulator so realism, championship-impact, etc. can be layered on the
    individual results client-side."""
    if db.get(Race, payload.race_id) is None:
        raise HTTPException(status_code=404, detail="Race not found")

    a = simulate_counterfactual(
        race_id=payload.race_id,
        changes=[c.model_dump() for c in payload.scenario_a],
    )
    b = simulate_counterfactual(
        race_id=payload.race_id,
        changes=[c.model_dump() for c in payload.scenario_b],
    )

    pos_a = _final_positions(a.get("alt_laps", []))
    pos_b = _final_positions(b.get("alt_laps", []))
    codes = sorted(set(pos_a) | set(pos_b))

    diff = []
    for code in codes:
        a_pos = pos_a.get(code)
        b_pos = pos_b.get(code)
        if a_pos is None or b_pos is None:
            delta = None
        else:
            delta = a_pos - b_pos  # negative = B is worse than A for this driver
        diff.append({"code": code, "a_pos": a_pos, "b_pos": b_pos, "delta": delta})

    # Order: biggest absolute swing first, retirees last
    def _sort_key(row):
        return (
            row["delta"] is None,
            -abs(row["delta"] or 0),
            row["code"],
        )

    diff.sort(key=_sort_key)

    return {
        "race_id": payload.race_id,
        "label_a": payload.label_a,
        "label_b": payload.label_b,
        "a": a,
        "b": b,
        "diff": diff,
    }


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
