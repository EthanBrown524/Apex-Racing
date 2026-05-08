from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Circuit


router = APIRouter(prefix="/circuits", tags=["circuits"])


@router.get("/{circuit_id}/path")
def get_circuit_path(circuit_id: int, db: Session = Depends(get_db)) -> dict:
    circuit = db.get(Circuit, circuit_id)
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")

    return {"circuit_id": circuit.id, "path": circuit.gps_path or []}

