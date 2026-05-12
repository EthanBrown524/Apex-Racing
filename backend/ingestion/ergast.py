from datetime import date
import os
import time

import requests
from sqlalchemy.orm import Session

from db.models import Circuit, Constructor, Driver, LapTime, PitStop, Race, RaceResult, Season


BASE_URL = os.getenv("ERGAST_BASE_URL", "https://api.jolpi.ca/ergast/f1")
REQUEST_PAUSE_SECONDS = 1.5
PAGE_LIMIT = 100
MAX_RETRIES = 5
RETRY_WAIT_SECONDS = 30


def _get_json(path: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(f"{BASE_URL}/{path}", timeout=30)
            if response.status_code == 429:
                wait = RETRY_WAIT_SECONDS * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s before retry {attempt + 1}/{MAX_RETRIES}...", flush=True)
                time.sleep(wait)
                continue
            response.raise_for_status()
            time.sleep(REQUEST_PAUSE_SECONDS)
            return response.json()["MRData"]
        except requests.exceptions.HTTPError as e:
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"  HTTP error: {e}, retrying in {RETRY_WAIT_SECONDS}s...", flush=True)
            time.sleep(RETRY_WAIT_SECONDS)
    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: {path}")


def _parse_time_ms(value: str | None) -> int | None:
    if not value:
        return None

    if ":" not in value:
        try:
            return round(float(value) * 1000)
        except ValueError:
            return None

    total_seconds = 0.0
    for part in value.split(":"):
        total_seconds = total_seconds * 60 + float(part)
    return round(total_seconds * 1000)


def _grid_position(value: str | None) -> int | None:
    if value in (None, "", "0"):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _upsert_season(db: Session, year: int) -> Season:
    season = db.get(Season, year)
    if season is None:
        season = Season(year=year)
        db.add(season)
    return season


def _upsert_driver_from_payload(db: Session, payload: dict) -> Driver:
    driver = db.query(Driver).filter_by(driver_ref=payload["driverId"]).one_or_none()
    if driver is None:
        driver = Driver(driver_ref=payload["driverId"])
        db.add(driver)

    driver.code = payload.get("code") or driver.code
    driver.forename = payload.get("givenName") or driver.forename
    driver.surname = payload.get("familyName") or driver.surname
    driver.nationality = payload.get("nationality") or driver.nationality
    db.flush()
    return driver


def _upsert_constructor_from_payload(db: Session, payload: dict) -> Constructor:
    constructor = db.query(Constructor).filter_by(constructor_ref=payload["constructorId"]).one_or_none()
    if constructor is None:
        constructor = Constructor(constructor_ref=payload["constructorId"])
        db.add(constructor)

    constructor.name = payload.get("name") or constructor.name
    constructor.nationality = payload.get("nationality") or constructor.nationality
    db.flush()
    return constructor


def _race_for_round(db: Session, year: int, round_number: int) -> Race:
    race = db.query(Race).filter_by(season_year=year, round=round_number).one_or_none()
    if race is None:
        raise ValueError(f"Race metadata missing for {year} round {round_number}")
    return race


def ingest_season_metadata(db: Session, year: int = 2023) -> None:
    _upsert_season(db, year)
    ingest_drivers(db, year)
    ingest_constructors(db, year)
    ingest_races(db, year)
    db.commit()


def ingest_season(db: Session, year: int = 2023, rounds: list[int] | None = None) -> None:
    print(f"Ingesting {year} metadata", flush=True)
    ingest_season_metadata(db, year)
    race_query = db.query(Race).filter_by(season_year=year)
    if rounds:
        race_query = race_query.filter(Race.round.in_(rounds))

    for race in race_query.order_by(Race.round.asc()).all():
        # Skip if already fully ingested
        existing_results = db.query(RaceResult).filter_by(race_id=race.id).count()
        existing_laps = db.query(LapTime).filter_by(race_id=race.id).count()
        existing_pits = db.query(PitStop).filter_by(race_id=race.id).count()

        if existing_results > 0 and existing_laps > 0 and existing_pits > 0:
            print(f"Skipping {year} round {race.round}: {race.name} (already ingested)", flush=True)
            continue

        print(f"Ingesting {year} round {race.round}: {race.name}", flush=True)

        if existing_results == 0:
            ingest_race_results(db, year, race.round)
            db.commit()
            print("  results committed", flush=True)
        else:
            print("  results already exist, skipping", flush=True)

        if existing_laps == 0:
            ingest_lap_times(db, year, race.round)
            db.commit()
            print("  lap times committed", flush=True)
        else:
            print("  lap times already exist, skipping", flush=True)

        if existing_pits == 0:
            ingest_pit_stops(db, year, race.round)
            db.commit()
            print("  pit stops committed", flush=True)
        else:
            print("  pit stops already exist, skipping", flush=True)


def ingest_drivers(db: Session, year: int) -> None:
    data = _get_json(f"{year}/drivers.json")
    for item in data["DriverTable"]["Drivers"]:
        _upsert_driver_from_payload(db, item)


def ingest_constructors(db: Session, year: int) -> None:
    data = _get_json(f"{year}/constructors.json")
    for item in data["ConstructorTable"]["Constructors"]:
        _upsert_constructor_from_payload(db, item)


def ingest_races(db: Session, year: int) -> None:
    data = _get_json(f"{year}/races.json")
    for item in data["RaceTable"]["Races"]:
        circuit_data = item["Circuit"]
        circuit = db.query(Circuit).filter_by(name=circuit_data["circuitName"]).one_or_none()
        if circuit is None:
            circuit = Circuit(name=circuit_data["circuitName"])
            db.add(circuit)
            db.flush()

        location = circuit_data.get("Location", {})
        circuit.location = location.get("locality")
        circuit.country = location.get("country")

        race = db.query(Race).filter_by(season_year=year, round=int(item["round"])).one_or_none()
        if race is None:
            race = Race(season_year=year, round=int(item["round"]))
            db.add(race)

        race.circuit_id = circuit.id
        race.name = item["raceName"]
        race.date = date.fromisoformat(item["date"])


def ingest_race_results(db: Session, year: int, round_number: int) -> None:
    race = _race_for_round(db, year, round_number)
    data = _get_json(f"{year}/{round_number}/results.json")
    races = data["RaceTable"].get("Races", [])
    if not races:
        return

    existing_results = {
        result.driver_id: result
        for result in db.query(RaceResult).filter_by(race_id=race.id).all()
    }
    for item in races[0].get("Results", []):
        driver = _upsert_driver_from_payload(db, item["Driver"])
        constructor = _upsert_constructor_from_payload(db, item["Constructor"])

        result = existing_results.get(driver.id)
        if result is None:
            result = RaceResult(race_id=race.id, driver_id=driver.id)
            db.add(result)
            existing_results[driver.id] = result

        result.constructor_id = constructor.id
        result.grid_position = _grid_position(item.get("grid"))
        result.final_position = int(item["position"])
        result.points = float(item.get("points") or 0)
        result.status = item.get("status")
        race.total_laps = max(race.total_laps or 0, int(item.get("laps") or 0)) or race.total_laps


def ingest_lap_times(db: Session, year: int, round_number: int) -> None:
    race = _race_for_round(db, year, round_number)
    offset = 0
    cumulative_by_driver: dict[int, int] = {}
    max_lap = race.total_laps or 0
    driver_cache = {driver.driver_ref: driver for driver in db.query(Driver).all()}
    lap_cache = {
        (lap_time.driver_id, lap_time.lap): lap_time
        for lap_time in db.query(LapTime).filter_by(race_id=race.id).all()
    }

    while True:
        data = _get_json(f"{year}/{round_number}/laps.json?limit={PAGE_LIMIT}&offset={offset}")
        races = data["RaceTable"].get("Races", [])
        lap_rows = races[0].get("Laps", []) if races else []
        if not lap_rows:
            break

        for lap_payload in lap_rows:
            lap_number = int(lap_payload["number"])
            lap_entries = []

            for timing in lap_payload.get("Timings", []):
                driver = driver_cache.get(timing["driverId"])
                if driver is None:
                    driver = Driver(driver_ref=timing["driverId"], code=timing["driverId"][:3].upper())
                    db.add(driver)
                    db.flush()
                    driver_cache[driver.driver_ref] = driver

                time_ms = _parse_time_ms(timing.get("time"))
                if time_ms is not None:
                    cumulative_by_driver[driver.id] = cumulative_by_driver.get(driver.id, 0) + time_ms

                lap_entries.append((driver, timing, time_ms, cumulative_by_driver.get(driver.id)))

            valid_entries = [(d, t, tm, e) for d, t, tm, e in lap_entries if e is not None]
            if not valid_entries:
                continue

            leader_elapsed = min(elapsed for _, _, _, elapsed in valid_entries)

            for driver, timing, time_ms, elapsed in lap_entries:
                lap_time = lap_cache.get((driver.id, lap_number))
                if lap_time is None:
                    lap_time = LapTime(race_id=race.id, driver_id=driver.id, lap=lap_number)
                    db.add(lap_time)
                    lap_cache[(driver.id, lap_number)] = lap_time

                lap_time.position = int(timing["position"])
                lap_time.time_ms = time_ms
                lap_time.gap_to_leader_ms = None if elapsed is None else elapsed - leader_elapsed

            max_lap = max(max_lap, lap_number)

        total = int(data.get("total", 0))
        offset += PAGE_LIMIT
        if offset >= total:
            break

    if max_lap:
        race.total_laps = max_lap


def ingest_pit_stops(db: Session, year: int, round_number: int) -> None:
    race = _race_for_round(db, year, round_number)
    data = _get_json(f"{year}/{round_number}/pitstops.json")
    races = data["RaceTable"].get("Races", [])
    if not races:
        return

    driver_cache = {driver.driver_ref: driver for driver in db.query(Driver).all()}
    pit_cache = {
        (stop.driver_id, stop.stop_number): stop
        for stop in db.query(PitStop).filter_by(race_id=race.id).all()
    }
    for item in races[0].get("PitStops", []):
        driver = driver_cache.get(item["driverId"])
        if driver is None:
            driver = Driver(driver_ref=item["driverId"], code=item["driverId"][:3].upper())
            db.add(driver)
            db.flush()
            driver_cache[driver.driver_ref] = driver

        stop_number = int(item["stop"])
        stop = pit_cache.get((driver.id, stop_number))
        if stop is None:
            stop = PitStop(race_id=race.id, driver_id=driver.id, stop_number=stop_number)
            db.add(stop)
            pit_cache[(driver.id, stop_number)] = stop

        stop.lap = int(item["lap"])
        stop.duration_ms = _parse_time_ms(item.get("duration"))