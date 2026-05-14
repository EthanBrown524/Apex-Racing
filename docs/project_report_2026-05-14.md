# APEX Racing Records Project Report

Date: 2026-05-14

## Fix Pass Completed

After this report was created, a targeted cleanup pass fixed several P0/P1 items:

- Added the missing Alembic migration for `circuits.gps_image`.
- Added `.env.example` and updated setup instructions.
- Added a flat ESLint config and restored `npm run lint`.
- Removed broken/encoding-damaged UI text from frontend source.
- Removed the duplicate circuit-scoped telemetry route.
- Added 404 validation for missing races/circuits on key API routes.

Still remaining:

- Forecast, RAG, FIA PDF parsing, scenario load/save, tire compound ingestion, test coverage, and bundle splitting.

## Executive Summary

APEX is in a solid foundation stage: the FastAPI service, SQLAlchemy models, Alembic migration, Ergast ingestion, FastF1 telemetry scripts, React/Vite frontend, replay canvas, counterfactual endpoint, and forecast page all exist. The main replay path is close to demonstrable when the database is populated.

The biggest risks are not broad architecture problems. They are integration drift and unfinished contracts:

- The database model and initial migration have already diverged.
- The frontend contains visible mojibake text from encoding damage.
- Linting is configured as a script but cannot run.
- Forecast, RAG, FIA PDF parsing, and real scenario workflows are placeholders.
- The app still relies on sample data fallbacks for important product states.

The next best milestone is to make the current replay app reliable end to end before expanding AI behavior.

## Confirmed Validation Results

- `npm run build` in `frontend/` succeeds.
- Vite reports a bundle warning: the main JS chunk is larger than 500 kB after minification.
- `npm run lint` in `frontend/` fails because ESLint 10 requires `eslint.config.js`, and the repo does not have one.
- A no-bytecode Python syntax pass over project backend files succeeds.
- `python -m compileall backend` is not a useful validation command right now because it traverses `backend/.venv` and `backend/%SystemDrive%`, then hits locked `__pycache__` writes.

## What Needs To Be Fixed

### P0: Database Schema Drift

`backend/db/models.py` defines `Circuit.gps_image`, and `backend/ingestion/run_circuits_all.py` writes `circuit.gps_image`. The initial Alembic migration only creates `circuits.gps_path`, not `circuits.gps_image`.

Why it matters:

- A fresh database created from migrations will not have the `gps_image` column.
- Any code path that persists rendered circuit images can fail at runtime.

Fix:

- Add a new Alembic migration for `circuits.gps_image`.
- Do not edit the already-applied initial migration unless this database has never been shared.
- Add a quick migration smoke check to the setup docs.

Relevant files:

- `backend/db/models.py`
- `backend/db/migrations/versions/c254d08a60f5_initial_schema.py`
- `backend/ingestion/run_circuits_all.py`

### P0: Frontend Encoding Damage

Several JSX/CSS files contain mojibake sequences where dashes, check marks, play/pause labels, or arrows were intended. These will show up as broken UI text.

Fix:

- Replace corrupted visible strings with ASCII text or proper UTF-8 symbols.
- Prefer text labels or icon components consistently.
- Scan the repo for common mojibake markers after fixing.

Relevant files:

- `frontend/src/pages/RewindPage.jsx`
- `frontend/src/components/PlaybackControls/PlaybackControls.jsx`
- `frontend/src/components/TrackCanvas/TrackCanvas.jsx`
- `frontend/src/components/WhatIfPanel/WhatIfPanel.jsx`
- `frontend/src/components/Leaderboard/Leaderboard.jsx`
- `frontend/src/styles.css`
- `backend/ingestion/run_telemetry.py`
- `backend/ingestion/run_circuits_all.py`

### P0: Lint Script Is Broken

`frontend/package.json` has a `lint` script, but the installed ESLint version expects a flat config file.

Fix:

- Add `frontend/eslint.config.js`.
- Include React hooks and React refresh rules already installed in `devDependencies`.
- Consider pinning frontend dependencies instead of using `latest`.

Relevant files:

- `frontend/package.json`
- `frontend/package-lock.json`

### P1: Missing `.env.example`

`README.md` tells developers to create `.env` from `.env.example`, but no `.env.example` exists in the repo.

Fix:

- Add a safe `.env.example` with placeholder values for `DATABASE_URL`, `FRONTEND_URL`, `IBM_API_KEY`, `WATSONX_PROJECT_ID`, and `WATSONX_URL`.
- Keep real `.env` ignored.

Relevant files:

- `README.md`
- `.gitignore`

### P1: Backend Validation And Error Semantics

Some backend endpoints return placeholder or soft-failure responses where clients would benefit from explicit HTTP errors.

Examples:

- `counterfactual.simulate_counterfactual` returns a 200-shaped payload when the race is missing instead of a 404.
- Forecast accepts any `race_id` but does not validate the race exists.
- Circuit path returns an empty path for missing circuits instead of distinguishing "not found" from "no path yet."

Fix:

- Move request validation into API routers where possible.
- Use `HTTPException` for missing resources.
- Keep graceful AI fallback behavior only for AI service failures, not missing core data.

Relevant files:

- `backend/api/counterfactual.py`
- `backend/ai/counterfactual.py`
- `backend/api/forecast.py`
- `backend/api/circuits.py`

### P1: Duplicate Telemetry Endpoint

Telemetry is exposed in both:

- `GET /races/{race_id}/telemetry/{lap}`
- `GET /circuits/telemetry/{race_id}/{lap}`

Fix:

- Keep the race-scoped endpoint.
- Remove or deprecate the circuit-scoped telemetry endpoint.
- Update frontend client code to use one canonical path.

Relevant files:

- `backend/api/races.py`
- `backend/api/circuits.py`
- `frontend/src/api/apexClient.js`

### P1: Replay Data Completeness

The frontend still depends on sample race/lap/forecast data when APIs are empty or unavailable. That is useful during development, but it can hide incomplete ingestion and make the app look successful when the backend is not actually serving data.

Fix:

- Add explicit loading, empty, and API-unavailable states.
- Use sample data only in a clearly marked demo mode.
- Track ingestion completion by race: metadata, results, laps, pits, circuit path, telemetry paths.

Relevant files:

- `frontend/src/hooks/useRaceData.js`
- `frontend/src/hooks/useTelemetry.js`
- `frontend/src/pages/ForecastPage.jsx`
- `frontend/src/sampleData.js`

### P1: Tire Strategy Data Is Not Actually Populated

The schema and UI support tire fields, but Ergast pit stop ingestion does not populate `tire_in` or `tire_out`. The race laps API tries to expose `tire_out`, so the leaderboard often cannot show real tire compounds.

Fix:

- Decide the tire data source, likely FastF1 stint/lap data.
- Add ingestion for compound by driver/lap or stint.
- Return tire compound from the lap endpoint using actual stint data.

Relevant files:

- `backend/db/models.py`
- `backend/ingestion/ergast.py`
- `backend/ingestion/fastf1_loader.py`
- `backend/api/races.py`
- `frontend/src/components/Leaderboard/Leaderboard.jsx`

### P2: Build And Backend Test Coverage

There are no test scripts or test directories for the backend or frontend. The project can build, but behavior is unprotected.

Fix:

- Backend: add `pytest`, API tests with FastAPI `TestClient`, and unit tests for time parsing, ingestion upserts, and counterfactual recomputation.
- Frontend: add Vitest or React Testing Library for hooks/components, especially fallback states and counterfactual UI.
- CI: run backend syntax/tests, frontend lint, and frontend build.

### P2: Repository Hygiene

The repo contains local/generated directories under `backend/`, including `.venv`, `%SystemDrive%`, and `__pycache__`. They are ignored now, but they interfere with broad commands.

Fix:

- Remove generated caches and accidental local environment folders from the workspace when safe.
- Keep `.gitignore` entries for `backend/%SystemDrive%/`, `.venv/`, `__pycache__/`, and `*.pyc`.
- Prefer scoped validation commands that do not traverse local environments.

## What Needs To Be Implemented Next

### 1. Reliable Race Replay Milestone

Goal: one or more 2023 races can be replayed from real database data without sample fallbacks.

Implement:

- Ingestion status endpoint per race.
- Canonical telemetry endpoint.
- Circuit path coverage for target races.
- Real empty/loading/error UI states.
- Fix replay controls and encoded labels.
- Add a smoke script that verifies a selected race has laps, drivers, circuit path, and optional telemetry.

Recommended first target:

- One fully populated 2023 race, then expand to the whole 2023 season.

### 2. Scenario Save/Load Workflow

Goal: users can create, run, save, list, and reload what-if scenarios.

Implement:

- Scenario detail endpoint: `GET /scenarios/{id}`.
- Scenario delete endpoint.
- Save button after a simulation result.
- Load scenario into `WhatIfPanel`.
- Scenario labels generated from changes if the user does not provide one.

### 3. Counterfactual Simulation Upgrade

Goal: move from a basic deterministic demo to a race-plausible strategy model.

Implement:

- Validate driver codes and lap bounds.
- Model pit stop delta by race instead of global average only.
- Preserve DNFs and lapped-car behavior more carefully.
- Recompute classification from cumulative race time plus completed laps.
- Return structured deltas: position changes, time gained/lost, affected rivals, changed final top 10.
- Keep Granite as an explainer over computed facts, not as the source of truth.

### 4. Forecast Dashboard V1

Goal: replace placeholder forecast payloads with a real baseline model.

Implement:

- Build feature extraction from historical results, qualifying/grid, circuit traits, constructor/driver form, safety car rate, tire degradation proxy, and weather if available.
- Start with a transparent heuristic or simple statistical model before a more complex ML layer.
- Store forecast runs and feature snapshots.
- Return calibrated `win_pct`, `podium_pct`, strategy recommendation, and risk factors.

Relevant current placeholder:

- `backend/ai/forecast.py`

### 5. RAG And FIA Document Pipeline

Goal: make AI explanations cite real race context and FIA documents.

Implement:

- `fia_parser.py` with Docling extraction for FIA PDFs.
- Chunking and embedding ingestion into `race_embeddings`.
- pgvector similarity search in `ai/rag.py`.
- Prompt construction that includes retrieved context and strict citation metadata.
- Background ingestion command for new PDFs.

Relevant current placeholders:

- `backend/ingestion/fia_parser.py`
- `backend/ai/rag.py`
- `backend/db/models.py`

### 6. Developer Experience And Deployment

Goal: make the project easy to run from a clean checkout.

Implement:

- `.env.example`.
- `docker-compose.yml` for Postgres plus pgvector.
- Backend run script and frontend run script.
- Seed command for a known demo race.
- CI workflow.
- Clear README setup order: database, migrations, ingestion, backend, frontend.

## Suggested Next Work Order

1. Add the missing `gps_image` migration.
2. Fix mojibake text in frontend/backend visible output.
3. Add `frontend/eslint.config.js` and make `npm run lint` pass.
4. Add `.env.example` and update setup docs.
5. Remove duplicate telemetry endpoint or mark one deprecated.
6. Add race ingestion status endpoint and real frontend empty states.
7. Fully ingest one race and verify replay end to end.
8. Add focused backend and frontend tests around that race replay contract.
9. Implement scenario load/save workflow.
10. Replace forecast placeholder with a baseline forecast model.

## Current Project Health

- Architecture: good foundation.
- Frontend build: passes.
- Frontend lint: blocked by missing config.
- Backend syntax: project files parse.
- Backend runtime confidence: moderate, but depends on database/migration state.
- Data completeness: partial.
- AI readiness: early placeholder stage.
- Best next milestone: make replay reliable with real data before expanding forecast/RAG.
