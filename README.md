# APEX Race Director

**An AI-powered Formula 1 alternate-history simulator.**
Built on the IBM watsonx + Granite stack for the IBM May 2026 hackathon.

APEX turns every Grand Prix from **2019-2024** into an editable timeline.
Replay any race with telemetry-driven cars and Granite-narrated commentary,
rewrite the strategy in the What-If Lab, watch the **season championship flip
in real time**, or ask **Glory Path** to find the smallest set of changes that
gets your favourite driver to P1.

## Modes

| Page | What it does |
|------|--------------|
| **Home** | Landing page - hero, scale strip, three pillars, AI-in-F1 narrative, featured demo scenarios, IBM stack cards. Surfaces a banner when ingestion is incomplete. |
| **Seasons** | Six rich year cards (2019-2024) - champion, tagline, narrative, iconic moment, ingestion progress bar. Primary year-selection surface. |
| **Library** | Race grid filtered by year + free-text search. Scoped by `/seasons/:year`. |
| **Showcase** | One-click curated demos: Abu Dhabi 2021, Monaco 2022, Singapore 2023 in the wet, Glory Path for Alonso, and more. `/showcase?auto=1` cycles every 6s for a **hands-free demo**. |
| **Time Machine** | Replay a race with telemetry, live leaderboard, lap-by-lap Granite commentary, free-form "Ask APEX" Q&A, optional synthesized **engine drone**, and keyboard shortcuts. |
| **What-If Lab** | Apply pit / DNF / weather / safety-car / mechanical / grid-swap / fastest-lap changes. Safety car bunches the field to a ≤1.5s gap window. Toggle **AI Race Director** to have Granite plan per-driver strategic responses to your trigger. Granite explains the outcome with citations; **Realism Score** chip rates plausibility; **Championship Impact** card recomputes the season standings. |
| **Compare** | Two `WhatIfPanel`s side-by-side; runs both scenarios and shows a per-driver position delta table. |
| **Glory Path** | Pick a driver + target finish. Greedy optimizer finds the minimum interventions; Granite narrates and rewrites each rationale in **coach-me** style; animated `P-start -> P-achieved` hero. Solved paths persist as Scenarios. |
| **Driver** | `/driver/:code/:year` - season hero, cumulative-points line chart, race-by-race table. Reachable from any leaderboard. |
| **Standings** | `/standings/:year` - drivers' championship table aggregated client-side from per-driver season-points. |
| **Forecast** | Win-probability bars + circuit-DNA radar. When IBM creds are present, Granite re-ranks and rewrites the strategy lines; otherwise the heuristic runs. Chip shows which path served the response. |
| **Stats** | Scale showcase - animated big numbers (Grand Prix, laps, pit stops, telemetry points, RAG chunks) + per-season progress bars. |

## IBM stack

- **Granite-3-8b-instruct** (watsonx.ai) - explanations, narration, Q&A, storylines, realism scoring, **streaming** "Ask APEX" responses, forecast re-ranking, Glory Path coach-me rewrite, Race Director planning.
- **Slate-30m-english-rtrvr** (watsonx.ai embeddings) - RAG over race narratives + FIA stewards' decisions + technical regulations.
- **Docling** - FIA PDF -> structured markdown -> RAG chunks. Drop PDFs into `backend/fia_pdfs/` per [`docs/FIA_INGESTION.md`](docs/FIA_INGESTION.md).
- **Langflow** - exportable visual graphs of the counterfactual, glory-path, and forecast pipelines (`langflow/*.json`).

## Architecture

```
React (Vite) <--> FastAPI <--> PostgreSQL + pgvector
                      |
                      +--> watsonx.ai (Granite + Slate)
                      +--> Docling (FIA PDFs)
                      +--> FastF1 / Ergast (ingestion)
```

12 FastAPI routers, 14 AI modules, 10 smoke test files (94 tests, all DB-free), ~6000 backend + ~2700 frontend LOC.

## Docs

| Doc | Purpose |
|-----|---------|
| [`docs/APEX_Technical_Document_v2.md`](docs/APEX_Technical_Document_v2.md) | Full technical spec (architecture, data model, IBM stack, API contract, performance notes, demo script, tests). |
| [`docs/SETUP_AND_INGEST.md`](docs/SETUP_AND_INGEST.md) | Step-by-step setup + 2019-2024 ingestion runbook. |
| [`docs/ROADMAP_FOR_CLAUDE.md`](docs/ROADMAP_FOR_CLAUDE.md) | Tasks for follow-on agents with files, instructions, and acceptance checks. |

## Setup (TL;DR)

```bash
cp .env.example .env

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
npm run dev
```

## Ingest the 2019-2024 data

```bash
cd backend

# fastest: 3 seasons in parallel, skip telemetry
python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024 \
  --skip-telemetry --skip-embeddings --parallel-years 3

# add the AI/RAG index
python -m ingestion.embed_races --years 2019 2020 2021 2022 2023 2024

# backfill tire compounds + safety car windows from FastF1
python -m ingestion.run_tires --years 2019 2020 2021 2022 2023 2024

# check what got ingested
python -m ingestion.status

# (optional) backup the DB so you can restore on a demo laptop
python -m ingestion.export --out apex_dump.json
```

The pipeline shows tqdm progress bars and is restart-safe. See [`docs/SETUP_AND_INGEST.md`](docs/SETUP_AND_INGEST.md) for the full runbook.

## Run the tests

```bash
cd backend
pytest tests/ -v
```

The smoke test suite is organized across 10 test files and does not require
Postgres or IBM credentials.

## Live diagnostics

`GET /health` returns row counts, season coverage, pgvector status, and
Granite credential status. The footer in the UI surfaces these as live
chips so judges can see what's wired at a glance.
