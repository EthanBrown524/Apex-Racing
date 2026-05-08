# APEX Racing Records - Updated Technical Foundation

Current as of: 2026-05-07  
Workspace: `D:\Projects\APEX-Racing Records`  
Purpose: technical handoff and critique document for human developers or AI models.

This document updates the original `APEX_Technical_Foundation.txt` with the actual implementation state, verified environment behavior, database status, known blockers, and recommended next engineering steps. It intentionally excludes secrets. Do not paste `.env` contents into external tools.

---

## 1. Product Goal

APEX Racing Records is a Formula 1 analytics application with two primary modules:

1. Race Rewind
   - Replay historical races lap by lap.
   - Visualize track position movement on a canvas.
   - Compare actual outcomes against counterfactual strategy changes.

2. Forecast
   - Predict upcoming or selected race outcomes.
   - Show driver probabilities, circuit characteristics, and risk factors.
   - Eventually use IBM Granite to generate natural-language reasoning from structured data and retrieved context.

The current implementation is a first working foundation, not a completed product. The database schema is live, the backend imports cleanly, and one real race has been ingested.

---

## 2. Current Architecture

```text
[External F1 APIs]
    |
    |-- Jolpica F1 API, Ergast-compatible
    |-- FastF1, planned for telemetry/GPS
    |-- OpenF1, planned for live/current-season data
    |-- FIA PDFs, planned for Docling parsing
    |
[Python Ingestion]
    |
[Supabase PostgreSQL + pgvector]
    |
[FastAPI Backend]
    |
[React + Vite Frontend]
```

Planned AI layer:

```text
[PostgreSQL relational race data]
[PostgreSQL pgvector retrieved text chunks]
        |
        v
[RAG context builder]
        |
        v
[IBM watsonx.ai / Granite]
        |
        v
[FastAPI explanation endpoints]
```

Important design principle:

The race math should stay deterministic and data-driven. AI should explain, summarize, and reason over computed outputs. It should not invent lap timing, finishing orders, or strategy deltas.

---

## 3. Technology Stack

### Implemented

- Python 3.13.13 available locally.
- FastAPI backend scaffold.
- SQLAlchemy 2 ORM models.
- Alembic migrations.
- Supabase PostgreSQL database.
- pgvector extension enabled.
- Python ingestion using `requests`.
- React/Vite-style frontend source scaffold.
- Canvas-based race visualization component with sample fallback data.

### Partially Implemented

- IBM Granite client scaffold exists but has not been called.
- Counterfactual API route exists but currently returns placeholder simulation output.
- Forecast API route exists but currently returns placeholder forecast output.
- FastF1 loader scaffold exists but has not been run against real telemetry.
- Langflow placeholder JSON files exist but are not real flows.

### Not Yet Implemented

- Real counterfactual simulation engine.
- Real forecasting model.
- IBM watsonx.ai integration test.
- Docling PDF parsing pipeline.
- RAG embedding generation.
- Frontend dependency install and browser verification.
- Full-season ingestion beyond one race.
- Authentication, deployment, CI, or production config.

---

## 4. Repository Structure

```text
APEX-Racing Records/
|-- .env                         # local secrets, gitignored
|-- .env.example                 # safe template
|-- .gitignore
|-- README.md
|
|-- backend/
|   |-- main.py                  # FastAPI app entry point
|   |-- requirements.txt
|   |-- alembic.ini
|   |
|   |-- api/
|   |   |-- races.py             # GET /races, GET /races/{race_id}/laps
|   |   |-- circuits.py          # GET /circuits/{circuit_id}/path
|   |   |-- counterfactual.py    # POST /counterfactual/simulate
|   |   |-- forecast.py          # GET /forecast/{race_id}
|   |   `-- scenarios.py         # POST/GET /scenarios
|   |
|   |-- db/
|   |   |-- connection.py        # SQLAlchemy engine/session/dependency
|   |   |-- models.py            # ORM schema
|   |   `-- migrations/
|   |       |-- env.py
|   |       |-- script.py.mako
|   |       `-- versions/
|   |           `-- c254d08a60f5_initial_schema.py
|   |
|   |-- ingestion/
|   |   |-- ergast.py            # Jolpica/Ergast-compatible ingestion
|   |   |-- run_all.py           # CLI entry point
|   |   |-- fastf1_loader.py
|   |   |-- openf1.py
|   |   `-- fia_parser.py
|   |
|   |-- ai/
|   |   |-- granite.py           # IBM token refresh and text generation scaffold
|   |   |-- counterfactual.py    # placeholder
|   |   |-- forecast.py          # placeholder
|   |   `-- rag.py               # placeholder
|   |
|   `-- utils/
|       |-- normalize.py
|       `-- cache.py
|
|-- frontend/
|   |-- package.json
|   |-- vite.config.js
|   |-- index.html
|   `-- src/
|       |-- App.jsx
|       |-- main.jsx
|       |-- styles.css
|       |-- sampleData.js
|       |-- api/apexClient.js
|       |-- hooks/useRaceData.js
|       |-- hooks/useCounterfactual.js
|       |-- pages/RewindPage.jsx
|       |-- pages/ForecastPage.jsx
|       `-- components/
|
|-- docs/
|   |-- architecture.md
|   |-- data_schema.md
|   `-- APEX_Updated_Technical_Foundation.md
|
|-- langflow/
|   |-- counterfactual_flow.json
|   `-- forecast_flow.json
|
`-- fia_pdfs/
```

Known local artifact:

- `backend/%SystemDrive%/` was generated during an earlier failed process-launch experiment. It is now gitignored. It may require Windows/admin cleanup because it contains Windows cache-like files with restricted permissions.

---

## 5. Environment Configuration

### `.env`

The real `.env` exists locally and is gitignored.

Expected keys:

```env
DATABASE_URL=postgresql+psycopg2://...
IBM_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://us-south.ml.cloud.ibm.com
LANGFLOW_URL=http://localhost:7860
FRONTEND_URL=http://localhost:5173
ERGAST_BASE_URL=https://api.jolpi.ca/ergast/f1
```

Current database choice:

- Supabase PostgreSQL
- Session pooler connection string
- SQLAlchemy URL format
- pgvector enabled

Why Supabase was chosen:

- Hosted PostgreSQL avoids local Windows Postgres/pgvector setup friction.
- Supabase includes pgvector support.
- Easier project handoff/demo than local-only database.

---

## 6. Database

### Database Provider

Supabase PostgreSQL, using the session pooler endpoint.

### Migration State

Current Alembic revision:

```text
c254d08a60f5
```

Migration file:

```text
backend/db/migrations/versions/c254d08a60f5_initial_schema.py
```

The migration:

- Creates all core tables.
- Ensures `CREATE EXTENSION IF NOT EXISTS vector`.
- Creates standard lookup/performance indexes.
- Creates an ivfflat vector index for `race_embeddings.embedding`.

### Tables

Implemented tables:

```text
circuits
drivers
constructors
seasons
races
race_results
lap_times
pit_stops
safety_cars
telemetry_paths
race_embeddings
scenarios
alembic_version
```

The original plan did not define a `scenarios` table even though it defined scenario endpoints. A `scenarios` table was added to persist user what-if changes.

### Verified Row Counts

Verified on 2026-05-07 after ingesting 2023 Bahrain Grand Prix:

```text
circuits=22
drivers=22
constructors=10
seasons=1
races=22
race_results=20
lap_times=1055
pit_stops=30
safety_cars=0
telemetry_paths=0
race_embeddings=0
scenarios=0
```

Interpretation:

- Full 2023 metadata is loaded: season, races, circuits, drivers, constructors.
- Detailed race data has only been loaded for 2023 round 1, Bahrain Grand Prix.
- Race replay data exists for Bahrain: 57 laps and 20 drivers.
- Safety car, telemetry, embeddings, and scenarios are not populated yet.

---

## 7. Backend Implementation

### Entry Point

File:

```text
backend/main.py
```

Implemented:

- `FastAPI(title="APEX Racing Records API", version="0.1.0")`
- CORS middleware using `FRONTEND_URL`.
- Router registration for races, circuits, counterfactuals, forecasts, scenarios.
- `GET /` health check returns `{"status": "ok"}`.

### Database Connection

File:

```text
backend/db/connection.py
```

Implemented:

- Loads `.env`.
- Reads `DATABASE_URL`.
- Creates SQLAlchemy `engine`.
- Creates `SessionLocal`.
- Provides `get_db()` dependency for FastAPI routes.

### ORM Models

File:

```text
backend/db/models.py
```

Implemented:

- SQLAlchemy 2 `DeclarativeBase`.
- Models for all database tables.
- PostgreSQL `JSONB`.
- `pgvector.sqlalchemy.Vector(1536)` for embeddings.
- Relationships for core race, driver, result, lap, and pit-stop entities.

Notable implementation detail:

- `RaceEmbedding.metadata` is mapped as `metadata_` in Python because SQLAlchemy reserves `metadata`.

### API Endpoints

Implemented route files:

```text
backend/api/races.py
backend/api/circuits.py
backend/api/counterfactual.py
backend/api/forecast.py
backend/api/scenarios.py
```

Current endpoint behavior:

```text
GET /races
```

Returns all races with:

```json
{
  "id": 1,
  "name": "Bahrain Grand Prix",
  "season": 2023,
  "round": 1,
  "circuit_id": 1,
  "circuit_name": "Bahrain International Circuit",
  "date": "2023-03-05",
  "total_laps": 57
}
```

```text
GET /races/{race_id}/laps
```

Returns:

```json
{
  "race_id": 1,
  "laps": [
    {
      "lap": 1,
      "drivers": [
        {
          "driver_id": 1,
          "code": "VER",
          "position": 1,
          "gap_ms": 0,
          "time_ms": 99671,
          "tire": null,
          "in_pit": false
        }
      ]
    }
  ]
}
```

```text
GET /circuits/{circuit_id}/path
```

Returns normalized circuit path when present. Currently most circuits have no `gps_path` because FastF1 path ingestion has not been run.

```text
POST /counterfactual/simulate
```

Accepts the intended request shape but returns placeholder output.

```text
GET /forecast/{race_id}
```

Returns placeholder prediction structure.

```text
POST /scenarios
GET /scenarios
```

Implemented against the `scenarios` table.

### Backend Validation Completed

Verified:

- Project Python files parse.
- Backend app imports.
- SQLAlchemy can connect to Supabase.
- pgvector extension is available.
- Alembic migration applied.
- API function-level smoke test returned:

```text
races 22
first race Bahrain Grand Prix
total_laps 57
laps 57
drivers lap1 20
```

Not yet verified:

- Live `uvicorn` server running in browser.
- `/docs` loaded in browser.
- End-to-end frontend-to-backend calls.

---

## 8. Ingestion

### Data Source Decision

The original document referenced Ergast:

```text
http://ergast.com/api/f1
```

The implementation now uses Jolpica F1:

```text
https://api.jolpi.ca/ergast/f1
```

Reason:

- Jolpica provides an Ergast-compatible API path.
- Ergast has been deprecated/replaced for ongoing use.
- The response shape remains `MRData`, so the original ingestion architecture still applies.

### Implemented Ingestion

File:

```text
backend/ingestion/ergast.py
```

Implemented functions:

```python
ingest_season_metadata(db, year=2023)
ingest_season(db, year=2023, rounds=None)
ingest_drivers(db, year)
ingest_constructors(db, year)
ingest_races(db, year)
ingest_race_results(db, year, round_number)
ingest_lap_times(db, year, round_number)
ingest_pit_stops(db, year, round_number)
```

CLI entry point:

```text
backend/ingestion/run_all.py
```

Usage from `backend/`:

```powershell
.\.venv\Scripts\python.exe -B -m ingestion.run_all --year 2023 --round 1
```

What is loaded:

- Season row.
- Drivers.
- Constructors.
- Race metadata.
- Race results.
- Lap times.
- Derived cumulative gap to leader per lap.
- Pit stops.

Current limitations:

- Tire compounds are not available from Jolpica pit-stop payloads, so `tire_in` and `tire_out` remain null.
- Safety car periods are not loaded.
- Weather is not loaded.
- FastF1 telemetry path ingestion is separate and not yet run.
- There is no robust retry/backoff strategy beyond request timeouts and a 0.5 second pause.

Performance note:

The first ingestion version was too slow because it did remote database lookups inside the lap loop. It was optimized by caching driver and lap rows locally before processing lap pages.

---

## 9. Frontend Implementation

### Current State

The frontend source exists but dependencies have not been installed in this environment because `npm` was not callable here.

Files:

```text
frontend/package.json
frontend/vite.config.js
frontend/index.html
frontend/src/main.jsx
frontend/src/App.jsx
frontend/src/styles.css
frontend/src/sampleData.js
frontend/src/api/apexClient.js
frontend/src/hooks/useRaceData.js
frontend/src/hooks/useCounterfactual.js
frontend/src/pages/RewindPage.jsx
frontend/src/pages/ForecastPage.jsx
frontend/src/components/*
```

Implemented UI:

- App shell with navigation.
- Race Rewind page.
- Forecast page.
- TrackCanvas component using Canvas 2D.
- Animation hook using `requestAnimationFrame`.
- Leaderboard.
- Playback controls.
- What-if panel.
- Circuit DNA radar chart.
- Forecast dashboard.
- Axios client.
- Hooks that use backend data when available and sample data as fallback.

Not yet verified:

- `npm install`
- `npm run dev`
- Vite build
- Browser render
- Canvas visual QA
- Real API-driven frontend state

Known local issue:

- `node.exe` exists, but `npm` was not found from the Codex shell. The user should verify Node.js/npm installation in normal PowerShell.

Recommended user check:

```powershell
node --version
npm --version
```

---

## 10. IBM Technology Plan

No IBM services have been called yet.

Planned IBM components:

1. IBM Cloud IAM
   - Exchange `IBM_API_KEY` for an access token.
   - Token refresh should occur before 55 minutes.

2. IBM watsonx.ai
   - Host model inference endpoint.

3. IBM Granite
   - Planned model: `ibm/granite-13b-chat-v2` from the original document.
   - Use cases:
     - counterfactual explanation
     - forecast explanation
     - risk-factor summaries
     - FIA/regulation-grounded reasoning

4. IBM Docling
   - Parse FIA PDFs into structured text.
   - Feed chunks into RAG pipeline.

5. RAG over PostgreSQL/pgvector
   - Store text chunks in `race_embeddings`.
   - Retrieve relevant text for a given race, strategy, incident, or regulation question.
   - Send retrieved context plus computed race facts to Granite.

Implemented files:

```text
backend/ai/granite.py
backend/ai/rag.py
backend/ingestion/fia_parser.py
```

Current IBM implementation state:

- `granite.py` includes a client scaffold with token refresh and generation call shape.
- No credentials have been added.
- No IBM endpoint has been called.
- No Docling parsing has been run.
- No embeddings have been generated.

---

## 11. Commands That Worked

From project root:

```powershell
backend\.venv\Scripts\python.exe -B -c "import sys; sys.path.insert(0, 'backend'); import main; print(main.app.title)"
```

Result:

```text
APEX Racing Records API
```

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Result:

```text
Running upgrade -> c254d08a60f5, initial schema
```

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -B -m ingestion.run_all --year 2023 --round 1
```

Result:

```text
Ingesting 2023 metadata
Ingesting 2023 round 1: Bahrain Grand Prix
  results committed
  lap times committed
  pit stops committed
```

---

## 12. Known Problems And Risks

### 1. Frontend Dependencies Not Installed

Impact:

- Cannot run or build frontend yet.
- Canvas and responsive UI are source-complete but not browser-verified.

Likely fix:

Install or repair Node.js/npm locally, then run:

```powershell
cd "D:\Projects\APEX-Racing Records\frontend"
npm install
npm run dev
```

### 2. Backend Server Not Running Persistently

Impact:

- API is verified through imports/function calls, not through a live HTTP server.

Recommended command:

```powershell
cd "D:\Projects\APEX-Racing Records\backend"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Circuit Paths Empty

Impact:

- Real backend `GET /circuits/{id}/path` returns empty arrays until FastF1 path ingestion is done.
- Frontend currently uses sample circuit path fallback.

Recommended fix:

Use FastF1 to load one representative lap path per race/circuit, normalize it, and store it in `circuits.gps_path`.

### 4. Counterfactual Logic Is Placeholder

Impact:

- UI can submit what-if changes, but backend does not compute alternate lap results.

Recommended fix:

Create a deterministic simulation layer before Granite explanation.

### 5. Forecast Logic Is Placeholder

Impact:

- Forecast dashboard source exists, but backend returns no real prediction rows.

Recommended fix:

Start with heuristic/model-free probabilities using recent form, qualifying/grid once available, constructor pace, circuit type, pit-stop loss, and safety-car history.

### 6. Data Model Needs Iteration

Potential additions:

- `driver_stints`
- `tire_compounds`
- `qualifying_results`
- `practice_results`
- `weather_observations`
- `race_control_messages`
- `track_status_periods`
- `team_radio`
- `model_runs`
- `forecast_snapshots`

### 7. Security And Secret Handling

Current:

- `.env` is gitignored.
- `.env.example` exists.

Risk:

- Other AI models should not receive real `.env` content.
- Supabase password must not be committed.

### 8. Local Filesystem Artifacts

`backend/%SystemDrive%/` exists from a failed process launch and is gitignored. It may require manual cleanup outside Codex if desired.

---

## 13. Immediate Next Steps

### Step 1: Backfill 2023 Race Details

Goal:

Load all 2023 results, lap times, and pit stops.

Command:

```powershell
cd "D:\Projects\APEX-Racing Records\backend"
.\.venv\Scripts\python.exe -B -m ingestion.run_all --year 2023
```

Expected:

- 22 races already exist.
- Race results should grow to roughly 440 rows.
- Lap times should grow substantially.
- Pit stops should grow for all races.

Risk:

- Full-season ingest may take several minutes.
- Network interruptions should be handled better before multi-season backfill.

### Step 2: Start Backend Server

```powershell
cd "D:\Projects\APEX-Racing Records\backend"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verify:

```text
http://localhost:8000/
http://localhost:8000/docs
http://localhost:8000/races
```

### Step 3: Fix/Verify Node And Run Frontend

```powershell
node --version
npm --version
cd "D:\Projects\APEX-Racing Records\frontend"
npm install
npm run dev
```

Verify:

```text
http://localhost:5173
```

### Step 4: Store Real Circuit Paths

Start with Bahrain 2023:

- Load FastF1 session.
- Pick a representative driver/lap.
- Extract `X`, `Y`, `Distance`, `Speed`.
- Normalize to 0-1.
- Store outline in `circuits.gps_path`.
- Optionally store per-lap data in `telemetry_paths`.

### Step 5: Implement Minimal Counterfactual Engine

First deterministic version:

- Input: race id and list of changes.
- Load actual lap timings.
- Apply a pit-stop delta or DNF event.
- Recompute cumulative elapsed time.
- Re-rank drivers by cumulative elapsed time per lap.
- Return `alt_laps` in the same shape as `/races/{race_id}/laps`.

Recommended first supported change:

```json
{
  "driver_code": "HAM",
  "change_type": "pit_lap",
  "lap": 14,
  "value": 19
}
```

### Step 6: Add Granite Explanation

Only after deterministic simulation works:

- Pass actual vs alternate summary to Granite.
- Ask Granite for short explanation grounded only in provided facts.
- Return explanation alongside `alt_laps`.

### Step 7: Build RAG Later

RAG should wait until:

- Race replay works.
- Counterfactual math works.
- Basic forecast works.

Then:

- Parse FIA PDFs with Docling.
- Chunk parsed text.
- Generate embeddings.
- Store in `race_embeddings`.
- Retrieve relevant chunks for Granite.

---

## 14. Suggested Critique Questions For Other AI Models

Ask another model to review:

1. Is the current schema sufficient for accurate lap-by-lap counterfactual simulation?
2. What tables are missing for F1 tire strategy analysis?
3. Should `lap_times.gap_to_leader_ms` be stored or derived on request?
4. Should circuit GPS paths live on `circuits` or in a separate versioned table?
5. What is the cleanest deterministic model for pit-lap counterfactuals without overfitting?
6. How should race-control and safety-car periods be represented?
7. What minimum telemetry should be ingested from FastF1 for a useful canvas replay?
8. What is the right boundary between deterministic logic and IBM Granite generation?
9. How should embeddings be generated and versioned?
10. What test suite should be added before implementing forecast logic?

---

## 15. Recommended Engineering Priorities

Priority order:

1. Complete 2023 ingestion.
2. Run backend via HTTP and verify docs.
3. Install frontend dependencies and verify visual app.
4. Ingest one real circuit path.
5. Replace sample canvas path with backend path.
6. Build deterministic counterfactual engine.
7. Add tests around counterfactual ranking.
8. Add Granite explanation after deterministic results exist.
9. Add forecast baseline.
10. Add Docling/RAG pipeline.

Do not start with AI explanations before the structured race data and deterministic simulation are correct.

