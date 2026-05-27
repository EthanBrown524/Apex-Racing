from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Circuit

router = APIRouter(prefix="/circuits", tags=["circuits"])


@router.get("")
def list_circuits(db: Session = Depends(get_db)) -> list[dict]:
    circuits = db.query(Circuit).order_by(Circuit.name).all()
    return [
        {
            "id": circuit.id,
            "name": circuit.name,
            "location": circuit.location,
            "country": circuit.country,
            "has_path": bool(circuit.gps_path),
        }
        for circuit in circuits
    ]


@router.get("/{circuit_id}/path")
def get_circuit_path(circuit_id: int, db: Session = Depends(get_db)) -> dict:
    circuit = db.get(Circuit, circuit_id)
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    if not circuit.gps_path:
        return {"circuit_id": circuit_id, "name": circuit.name, "path": []}

    return {
        "circuit_id": circuit_id,
        "name": circuit.name,
        "path": circuit.gps_path,
    }
