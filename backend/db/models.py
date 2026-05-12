from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import TypeDecorator

    class Vector(TypeDecorator):
        impl = Text
        cache_ok = True

        def __init__(self, dimensions: int):
            super().__init__()
            self.dimensions = dimensions


class Base(DeclarativeBase):
    pass


class Circuit(Base):
    __tablename__ = "circuits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    length_km: Mapped[float | None] = mapped_column(Numeric(6, 3))
    gps_path: Mapped[list[dict] | None] = mapped_column(JSONB)
    gps_image: Mapped[str | None] = mapped_column(Text)

    races: Mapped[list["Race"]] = relationship(back_populates="circuit")


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String(3))
    forename: Mapped[str | None] = mapped_column(String(50))
    surname: Mapped[str | None] = mapped_column(String(50))
    nationality: Mapped[str | None] = mapped_column(String(50))

    results: Mapped[list["RaceResult"]] = relationship(back_populates="driver")
    lap_times: Mapped[list["LapTime"]] = relationship(back_populates="driver")
    pit_stops: Mapped[list["PitStop"]] = relationship(back_populates="driver")


class Constructor(Base):
    __tablename__ = "constructors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    constructor_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    nationality: Mapped[str | None] = mapped_column(String(50))

    results: Mapped[list["RaceResult"]] = relationship(back_populates="constructor")


class Season(Base):
    __tablename__ = "seasons"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    races: Mapped[list["Race"]] = relationship(back_populates="season")


class Race(Base):
    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("season_year", "round", name="uq_race_season_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season_year: Mapped[int | None] = mapped_column(ForeignKey("seasons.year"))
    round: Mapped[int | None] = mapped_column(Integer)
    circuit_id: Mapped[int | None] = mapped_column(ForeignKey("circuits.id"))
    name: Mapped[str | None] = mapped_column(String(100))
    date: Mapped[datetime | None] = mapped_column(Date)
    total_laps: Mapped[int | None] = mapped_column(Integer)

    season: Mapped[Season | None] = relationship(back_populates="races")
    circuit: Mapped[Circuit | None] = relationship(back_populates="races")
    results: Mapped[list["RaceResult"]] = relationship(back_populates="race")
    lap_times: Mapped[list["LapTime"]] = relationship(back_populates="race")
    pit_stops: Mapped[list["PitStop"]] = relationship(back_populates="race")


class RaceResult(Base):
    __tablename__ = "race_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race_id: Mapped[int | None] = mapped_column(ForeignKey("races.id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"))
    constructor_id: Mapped[int | None] = mapped_column(ForeignKey("constructors.id"))
    grid_position: Mapped[int | None] = mapped_column(Integer)
    final_position: Mapped[int | None] = mapped_column(Integer)
    points: Mapped[float | None] = mapped_column(Numeric(4, 1))
    status: Mapped[str | None] = mapped_column(String(50))

    race: Mapped[Race | None] = relationship(back_populates="results")
    driver: Mapped[Driver | None] = relationship(back_populates="results")
    constructor: Mapped[Constructor | None] = relationship(back_populates="results")


class LapTime(Base):
    __tablename__ = "lap_times"
    __table_args__ = (UniqueConstraint("race_id", "driver_id", "lap", name="uq_lap_driver_race"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race_id: Mapped[int | None] = mapped_column(ForeignKey("races.id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"))
    lap: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int | None] = mapped_column(Integer)
    time_ms: Mapped[int | None] = mapped_column(Integer)
    gap_to_leader_ms: Mapped[int | None] = mapped_column(Integer)

    race: Mapped[Race | None] = relationship(back_populates="lap_times")
    driver: Mapped[Driver | None] = relationship(back_populates="lap_times")


class PitStop(Base):
    __tablename__ = "pit_stops"
    __table_args__ = (UniqueConstraint("race_id", "driver_id", "stop_number", name="uq_pit_driver_stop"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race_id: Mapped[int | None] = mapped_column(ForeignKey("races.id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"))
    stop_number: Mapped[int | None] = mapped_column(Integer)
    lap: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    tire_in: Mapped[str | None] = mapped_column(String(10))
    tire_out: Mapped[str | None] = mapped_column(String(10))

    race: Mapped[Race | None] = relationship(back_populates="pit_stops")
    driver: Mapped[Driver | None] = relationship(back_populates="pit_stops")


class SafetyCar(Base):
    __tablename__ = "safety_cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race_id: Mapped[int | None] = mapped_column(ForeignKey("races.id"))
    type: Mapped[str | None] = mapped_column(String(10))
    lap_start: Mapped[int | None] = mapped_column(Integer)
    lap_end: Mapped[int | None] = mapped_column(Integer)


class TelemetryPath(Base):
    __tablename__ = "telemetry_paths"
    __table_args__ = (UniqueConstraint("race_id", "driver_id", "lap", name="uq_telemetry_driver_lap"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race_id: Mapped[int | None] = mapped_column(ForeignKey("races.id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"))
    lap: Mapped[int | None] = mapped_column(Integer)
    path: Mapped[list[dict] | None] = mapped_column(JSONB)


class RaceEmbedding(Base):
    __tablename__ = "race_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race_id: Mapped[int | None] = mapped_column(ForeignKey("races.id"))
    content: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    race_id: Mapped[int | None] = mapped_column(ForeignKey("races.id"))
    changes: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

