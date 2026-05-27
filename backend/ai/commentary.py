"""AI race commentary - turns a race's lap data into a narrative.

Two modes:
  * `narrate_race(race_id, lap)` - color commentary up to a given lap
  * `answer_question(race_id, question)` - free-form Q&A with RAG citations
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.granite import generate, generate_stream
from ai.rag import build_race_context
from db.connection import SessionLocal
from db.models import Driver, LapTime, PitStop, Race, SafetyCar


def _race_summary(db: Session, race_id: int, up_to_lap: int | None = None) -> dict:
    race = db.get(Race, race_id)
    if race is None:
        raise ValueError(f"Race {race_id} not found")

    pit_rows = db.execute(
        select(PitStop.lap, PitStop.driver_id, Driver.code, PitStop.tire_in, PitStop.tire_out)
        .join(Driver, PitStop.driver_id == Driver.id)
        .where(PitStop.race_id == race_id)
        .order_by(PitStop.lap.asc())
    ).all()

    lap_rows = db.execute(
        select(LapTime.lap, LapTime.position, LapTime.gap_to_leader_ms, Driver.code)
        .join(Driver, LapTime.driver_id == Driver.id)
        .where(LapTime.race_id == race_id)
        .order_by(LapTime.lap.asc(), LapTime.position.asc())
    ).all()

    sc_rows = db.execute(
        select(SafetyCar.type, SafetyCar.lap_start, SafetyCar.lap_end).where(
            SafetyCar.race_id == race_id
        )
    ).all()

    lap_top: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for lap, pos, _gap, code in lap_rows:
        if up_to_lap is not None and lap > up_to_lap:
            continue
        lap_top[lap].append((pos, code))

    laps_sorted = sorted(lap_top.keys())
    if not laps_sorted:
        return {
            "race": race,
            "leader_changes": [],
            "pit_calls": [],
            "safety_cars": [],
            "final": [],
        }

    leader_changes = []
    last_leader = None
    for lap in laps_sorted:
        ordered = sorted(lap_top[lap])
        leader = ordered[0][1] if ordered else None
        if leader and leader != last_leader:
            leader_changes.append((lap, leader))
            last_leader = leader

    pit_calls = [
        {"lap": lap, "driver": code, "tire_in": tin, "tire_out": tout}
        for lap, _did, code, tin, tout in pit_rows
        if up_to_lap is None or lap <= up_to_lap
    ]

    safety_cars = [
        {"type": tp, "lap_start": ls, "lap_end": le} for tp, ls, le in sc_rows
    ]

    final_lap = laps_sorted[-1]
    final_top = sorted(lap_top[final_lap])[:5]

    return {
        "race": race,
        "leader_changes": leader_changes,
        "pit_calls": pit_calls[:15],
        "safety_cars": safety_cars,
        "final": [code for _pos, code in final_top],
        "up_to_lap": up_to_lap or final_lap,
    }


def _commentary_prompt(summary: dict, context: str) -> str:
    race = summary["race"]
    leaders = ", ".join(f"L{lap} {code}" for lap, code in summary["leader_changes"][:6]) or "no lead changes"
    pits = ", ".join(f"L{p['lap']} {p['driver']}({p['tire_out'] or '?'})" for p in summary["pit_calls"][:8]) or "no pit calls"
    scs = ", ".join(f"{s['type']} L{s['lap_start']}-{s['lap_end']}" for s in summary["safety_cars"]) or "none"
    final = ", ".join(f"P{i+1} {c}" for i, c in enumerate(summary["final"])) or "tbd"

    return f"""You are an experienced Formula 1 broadcast commentator. Write 4-6 sentences of vivid play-by-play narrative covering the race up to lap {summary['up_to_lap']}. Be specific, factual, and grounded ONLY in the facts and retrieved context below. Do not invent positions, lap numbers, or incidents.

Race: {race.name} {race.season_year}
Lead changes: {leaders}
Pit calls: {pits}
Safety cars: {scs}
Top 5 at lap {summary['up_to_lap']}: {final}

Retrieved race documents:
{context}

Commentary:"""


def narrate_race(race_id: int, up_to_lap: int | None = None) -> dict:
    try:
        with SessionLocal() as db:
            summary = _race_summary(db, race_id, up_to_lap)
    except ValueError as exc:
        return {"narrative": str(exc), "citations": []}

    rag = build_race_context(
        race_id=race_id,
        query=f"Race story through lap {summary['up_to_lap']} - lead changes, pit strategy, incidents",
    )
    prompt = _commentary_prompt(summary, rag["context"])

    try:
        text_out = generate(prompt, max_new_tokens=180, temperature=0.45, timeout=18)
        narrative = text_out.strip()
    except Exception as exc:
        narrative = _fallback_narrative(summary, exc)

    return {
        "race_id": race_id,
        "up_to_lap": summary["up_to_lap"],
        "narrative": narrative,
        "citations": rag["citations"],
    }


def answer_question(race_id: int, question: str) -> dict:
    try:
        with SessionLocal() as db:
            summary = _race_summary(db, race_id)
    except ValueError as exc:
        return {"answer": str(exc), "citations": []}

    rag = build_race_context(race_id=race_id, query=question)
    final = ", ".join(f"P{i+1} {c}" for i, c in enumerate(summary["final"]))
    leaders = ", ".join(f"L{lap} {code}" for lap, code in summary["leader_changes"][:6]) or "no lead changes"

    prompt = f"""You are an expert F1 race analyst. Answer the user's question using ONLY the facts and retrieved context below. Cite sources by their [number] when you use them. If the answer isn't supported by the context, say so plainly.

Race: {summary['race'].name} {summary['race'].season_year}
Final top 5: {final}
Lead changes: {leaders}

Context:
{rag['context']}

Question: {question}

Answer:"""

    try:
        answer = generate(prompt, max_new_tokens=400, temperature=0.4).strip()
    except Exception as exc:
        answer = f"AI explanation unavailable: {exc}"

    return {
        "race_id": race_id,
        "question": question,
        "answer": answer,
        "citations": rag["citations"],
    }


def answer_question_stream(race_id: int, question: str):
    """Generator counterpart to answer_question. Yields successive text
    fragments and a final newline-separated JSON envelope carrying the
    citations after the answer body is exhausted.
    """
    try:
        with SessionLocal() as db:
            summary = _race_summary(db, race_id)
    except ValueError as exc:
        yield str(exc)
        return

    rag = build_race_context(race_id=race_id, query=question)
    final = ", ".join(f"P{i+1} {c}" for i, c in enumerate(summary["final"]))
    leaders = ", ".join(f"L{lap} {code}" for lap, code in summary["leader_changes"][:6]) or "no lead changes"

    prompt = f"""You are an expert F1 race analyst. Answer the user's question using ONLY the facts and retrieved context below. Cite sources by their [number] when you use them. If the answer isn't supported by the context, say so plainly.

Race: {summary['race'].name} {summary['race'].season_year}
Final top 5: {final}
Lead changes: {leaders}

Context:
{rag['context']}

Question: {question}

Answer:"""

    try:
        for chunk in generate_stream(prompt, max_new_tokens=400, temperature=0.4):
            if chunk:
                yield chunk
    except Exception as exc:
        yield f"\n\n(AI explanation unavailable: {exc})"

    # Emit the citations as a final SSE event prefixed with a sentinel so the
    # client can pluck them out without confusing them for answer text.
    import json
    yield "\n\n[[CITATIONS]]" + json.dumps(rag["citations"])


def _fallback_narrative(summary: dict, exc: Exception) -> str:
    race = summary["race"]
    final = ", ".join(f"P{i+1} {c}" for i, c in enumerate(summary["final"])) or "no result"
    leaders = ", ".join(f"L{lap} {code}" for lap, code in summary["leader_changes"][:4]) or "no recorded lead changes"
    return (
        f"At the {race.name} ({race.season_year}), through lap {summary['up_to_lap']}: "
        f"lead changes - {leaders}. Top 5: {final}. "
        f"(Granite narrative unavailable: {exc})"
    )
