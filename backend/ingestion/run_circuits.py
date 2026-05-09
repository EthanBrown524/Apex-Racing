import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.connection import SessionLocal
from ingestion.fastf1_loader import ingest_circuit_path


def main():
    parser = argparse.ArgumentParser(description="Ingest circuit GPS paths via FastF1")
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--round", type=int, required=True, dest="round_number")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print(f"Ingesting circuit path for {args.year} round {args.round_number}")
        ingest_circuit_path(db, args.year, args.round_number)
    finally:
        db.close()


if __name__ == "__main__":
    main()