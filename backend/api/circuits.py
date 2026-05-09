from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Circuit

router = APIRouter(prefix="/circuits", tags=["circuits"])


@router.get("/{circuit_id}/path")
def get_circuit_path(circuit_id: int, db: Session = Depends(get_db)):
    circuit = db.get(Circuit, circuit_id)
    if circuit is None or not circuit.gps_path:
        return {"circuit_id": circuit_id, "path": []}
    return {
        "circuit_id": circuit_id,
        "name": circuit.name,
        "path": circuit.gps_path,
    }


@router.get("/")
def list_circuits(db: Session = Depends(get_db)):
    circuits = db.query(Circuit).order_by(Circuit.name).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "location": c.location,
            "country": c.country,
            "has_path": bool(c.gps_path),
        }
        for c in circuits
    ]