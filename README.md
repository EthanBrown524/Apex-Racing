# APEX Race Director

**An AI-powered Formula 1 alternate-history simulator.**
Built on the IBM watsonx + Granite stack for the IBM May 2026 hackathon.

APEX turns every Grand Prix from **2019-2024** into an editable timeline. Replay
any race with telemetry-driven car positions and AI commentary, rewrite the
strategy in the What-If Lab, or ask **Glory Path** to find the smallest set of
changes that gets your favourite driver to P1.

## Modes

| Mode | What it does |
|------|--------------|
| **Library** | Browse every race 2019-2024 grouped by season. |
| **Time Machine** | Replay a race with telemetry, live leaderboard, Granite-narrated commentary, and free-form "Ask APEX" Q&A. |
| **What-If Lab** | Apply pit, DNF, weather, safety-car, mechanical, grid-swap, or fastest-lap changes; Granite explains the new outcome with citations. |
| **Glory Path** | Pick a driver + target finish. The greedy optimizer finds minimum interventions and Granite narrates the alternate storyline. |
| **Forecast** | Win-probability bars + circuit-DNA radar derived from historical aggregates. |

## IBM stack

- **Granite-3-8b-instruct** (watsonx.ai) - explanations, narration, Q&A, storylines.
- **Slate-30m-english-rtrvr** (watsonx.ai embeddings) - RAG over race narratives + FIA stewards' decisions.
- **Docling** - FIA PDF -> structured markdown -> RAG chunks.
- **Langflow** - exportable visual graphs of the counterfactual, glory-path, and forecast pipelines (`langflow/*.json`).

## Architecture

```
React (Vite) <--> FastAPI <--> PostgreSQL + pgvector
                      |
                      +--> watsonx.ai (Granite + Slate)
                      +--> Docling (FIA PDFs)
                      +--> FastF1 / Ergast (ingestion)
```

Full breakdown in [`docs/APEX_Technical_Document_v2.md`](docs/APEX_Technical_Document_v2.md).
Continuation roadmap in [`docs/ROADMAP_FOR_CLAUDE.md`](docs/ROADMAP_FOR_CLAUDE.md).

## Setup

```bash
cp .env.example .env
# Edit .env: IBM_API_KEY, WATSONX_PROJECT_ID are optional - everything still
# runs without them (Granite paths return a deterministic fallback).

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

## Ingest the 2019-2024 data

```bash
cd backend
python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024
python -m ingestion.embed_races --years 2019 2020 2021 2022 2023 2024
```

The pipeline is restart-safe. Skip slow phases with `--skip-telemetry` or `--skip-embeddings`.

## FIA stewards' decisions

Drop PDFs in `backend/fia_pdfs/` and run:
```bash
python -m ingestion.fia_parser backend/fia_pdfs/
```

Each PDF becomes RAG-retrievable; citations appear in the UI as `[n] fia_decision` chips.

## API

Documented in section 8 of [`docs/APEX_Technical_Document_v2.md`](docs/APEX_Technical_Document_v2.md).
The OpenAPI auto-docs are at `http://localhost:8000/docs` when the backend is running.
