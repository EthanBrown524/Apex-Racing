import argparse

from db.connection import SessionLocal
from ingestion.ergast import ingest_season


def main() -> None:
    parser = argparse.ArgumentParser(description="Run APEX data ingestion.")
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--round", type=int, action="append", dest="rounds")
    args = parser.parse_args()

    with SessionLocal() as db:
        ingest_season(db, year=args.year, rounds=args.rounds)


if __name__ == "__main__":
    main()
