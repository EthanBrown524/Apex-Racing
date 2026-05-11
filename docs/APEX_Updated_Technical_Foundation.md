# APEX Racing Records - Updated Technical Foundation

Current as of: 2026-05-09
Workspace: `D:\Projects\APEX-Racing Records`
Purpose: Technical handoff and critique document for human developers or AI models.

This document supersedes all previous versions. It reflects the actual verified implementation state as of today, including completed phases, the revised IBM technology plan, and the remaining roadmap.

Do not paste `.env` contents into external tools. All secrets are gitignored locally.

---

## 1. Product Goal

APEX Racing Records is a Formula 1 analytics web application with two primary modules:

**Race Rewind**
- Replay historical races lap by lap on an animated canvas.
- Visualize real circuit GPS geometry with speed-colored track surface.
- Show F1 car silhouettes colored by team, rotating in direction of travel.
- Compare actual race outcomes against user-defined counterfactual strategy changes.
- Ghost cars show alternate race positions when a what-if simulation runs.

**Forecast**
- Predict upcoming or selected race outcomes.
- Show driver win probabilities, circuit characteristics, and risk factors.
- IBM Granite generates natural-language reasoning from structured race data and retrieved context.

---

## 2. Current Architecture

```text
[External F1 APIs]
    |
    |-- Jolpica F1 API (Ergast-compatible) — race metadata, results, laps, pit stops
    |-- FastF1 — circuit GPS paths (telemetry X/Y/Speed/Distance)
    |-- OpenF1 — planned for live/current-season data
    |-- FIA PDFs — planned for Docling parsing
    |
[Python Ingestion Layer]
    |
[Supabase PostgreSQL + pgvector]
    |
[FastAPI Backend — localhost:8000]
    |
[React + Vite Frontend — localhost:5173]
```

**Planned IBM AI Layer:**

```text
[PostgreSQL relational race data]
[FIA PDFs parsed by IBM Docling]
[pgvector text chunk embeddings]
        |
        v
[RAG context builder]
        |
        v
[IBM Granite via IBM Bob]
        |
        v
[FastAPI explanation endpoints]
        |
        v
[Frontend explanation panels]
```

**Core design principle:**

Race math is deterministic and data-driven. IBM Granite explains, summarizes, and reasons over computed outputs. It never invents lap timing, finishing orders, or strategy deltas.

---

## 3. Technology Stack

### Fully Implemented and Verified

- Python 3.13 backend
- FastAPI with CORS middleware
- SQLAlchemy 2 ORM
- Alembic migrations (revision `c254d08a60f5`)
- Supabase PostgreSQL with pgvector extension enabled
- Jolpica F1 API ingestion — full 2023 season loaded
- FastF1 circuit GPS path ingestion — Bahrain 2023 stored (729 points)
- React + Vite frontend running at `localhost:5173`
- Axios API client with backend/sample data fallback
- Canvas-based race replay with real Bahrain GPS geometry
- Speed-colored track surface (blue=slow → red=fast) using real telemetry speed data
- F1 car silhouettes per driver, colored by 2023 team, rotating in direction of travel
- Team color system in `frontend/src/teamColors.js` covering 2023 season, extensible by year
- Deterministic counterfactual simulation engine — fully working
- What-If panel wired end-to-end: UI → API → simulation → ghost cars on canvas
- Leaderboard with team-colored driver tags, podium highlights, tire/pit badges
- Playback controls: play/pause, speed multiplier, lap scrubber

### Partially Implemented

- IBM Granite client (`backend/ai/granite.py`) — rewritten as synchronous, token auth verified working, generation call returns 403 pending WML provisioning
- IBM Bob integration — planned replacement for watsonx.ai direct endpoint
- Forecast API route — returns placeholder, no real model yet
- Circuit GPS paths — only Bahrain loaded, remaining 21 circuits need FastF1 ingestion
- Docling PDF parser scaffold exists, no real parsing run yet
- RAG pipeline scaffold exists, no embeddings generated yet

### Not Yet Implemented

- IBM Bob API integration for Granite generation
- Docling FIA PDF parsing pipeline
- RAG embedding generation and retrieval
- Real forecast model (heuristic baseline planned first)
- Qualifying/grid position data ingestion
- Tire compound data (not available from Jolpica)
- Safety car period ingestion
- Authentication, deployment, CI/CD

---

## 4. IBM Technology Plan

### Tools Being Used

The project requirement is to use at least one IBM tool. APEX will use three:

| Tool | Role | Status |
|------|------|--------|
| IBM Granite | Natural language explanation of race strategy and counterfactual outcomes | Auth token working, generation pending Bob integration |
| IBM Bob | Platform to access Granite models without requiring Watson Machine Learning provisioning | Not yet integrated |
| IBM Docling | Parse FIA regulation PDFs and steward decisions into structured text for RAG | Scaffold exists, not yet run |

### Why These Three

- **Granite** is the core AI model. It explains simulation results in plain English, which is the most user-visible IBM feature.
- **Bob** provides free 30-day Granite access without needing a provisioned Watson Machine Learning instance. This unblocks development immediately.
- **Docling** gives the RAG pipeline real regulatory and race document context, making Granite explanations grounded in official F1 sources rather than generic knowledge.

### Why Not Watson Machine Learning Directly

A direct watsonx.ai call was attempted and returned 403 Forbidden because a Watson Machine Learning service instance was not provisioned. IBM Bob provides the same Granite model access without that requirement and is listed as an approved tool for this project.

### Integration Plan

**Phase 3a — IBM Bob + Granite (next step)**
1. Sign up for IBM Bob 30-day trial at `bob.ibm.com/trial`
2. Get Bob API endpoint and credentials
3. Update `backend/ai/granite.py` to call Bob endpoint instead of watsonx.ai directly
4. Test with one real counterfactual explanation prompt
5. Wire explanation into `POST /counterfactual/simulate` response
6. Display explanation text in frontend simulation note panel

**Phase 3b — IBM Docling**
1. Source FIA race regulation PDFs and 2023 steward decision documents
2. Store in `fia_pdfs/` directory
3. Run Docling to parse PDFs into structured text
4. Chunk parsed text into segments
5. Generate embeddings using a suitable model
6. Store chunks + embeddings in `race_embeddings` table
7. Build retrieval function: given a race/driver/strategy query, fetch top-k relevant chunks
8. Pass retrieved chunks as context to Granite prompts

**Phase 3c — RAG Pipeline**
1. Build `backend/ai/rag.py` retrieval function against pgvector
2. Add context injection to counterfactual explanation prompts
3. Add context injection to forecast explanation prompts
4. Test that explanations reference actual FIA rules and race documents

### Granite Prompt Design Principle

Every Granite prompt must:
- Provide only computed facts as input (positions, times, deltas)
- Ask Granite to explain, not to compute
- Include a grounding instruction: "Base your explanation only on the facts provided"
- Keep max_new_tokens at 300-500 for explanation panels

Example prompt structure for counterfactual:

```text
You are an F1 race analyst. Based only on the following race data, explain in 2-3 sentences
what effect the strategy change had on the final result.

Actual result: VER P1, LEC P2, HAM P5
Alternate result (HAM pits lap 20 instead of lap 14): VER P1, HAM P2, LEC P3

Change applied: HAM pit_lap moved from lap 14 to lap 20.
Time delta: HAM gained 18.4 seconds on track by staying out longer.

Explanation:
```

---

## 5. Repository Structure

```text
APEX-Racing Records/
|-- .env                              # local secrets, gitignored
|-- .env.example                      # safe template
|-- .gitignore
|-- README.md
|-- fastf1_cache/                     # FastF1 session cache, gitignored
|
|-- backend/
|   |-- main.py                       # FastAPI app, CORS, router registration
|   |-- requirements.txt
|   |-- alembic.ini
|   |
|   |-- api/
|   |   |-- races.py                  # GET /races, GET /races/{id}/laps
|   |   |-- circuits.py               # GET /circuits/{id}/path, GET /circuits/
|   |   |-- counterfactual.py         # POST /counterfactual/simulate
|   |   |-- forecast.py               # GET /forecast/{race_id}
|   |   `-- scenarios.py              # POST/GET /scenarios
|   |
|   |-- db/
|   |   |-- connection.py
|   |   |-- models.py
|   |   `-- migrations/versions/
|   |       `-- c254d08a60f5_initial_schema.py
|   |
|   |-- ingestion/
|   |   |-- ergast.py                 # Full Jolpica ingestion — verified working
|   |   |-- run_all.py                # CLI: --year, --round
|   |   |-- run_circuits.py           # CLI: FastF1 GPS path ingestion
|   |   |-- fastf1_loader.py          # FastF1 session loader + path extractor
|   |   |-- openf1.py                 # Placeholder
|   |   `-- fia_parser.py             # Docling placeholder
|   |
|   |-- ai/
|   |   |-- granite.py                # Sync IBM token + generate — token verified
|   |   |-- counterfactual.py         # Full deterministic simulation engine
|   |   |-- forecast.py               # Placeholder
|   |   `-- rag.py                    # Placeholder
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
|       |-- App.jsx                   # Brand header, nav, routes
|       |-- main.jsx
|       |-- styles.css                # Full dark F1 theme
|       |-- sampleData.js             # Fallback data when API unavailable
|       |-- teamColors.js             # Team colors + driver mapping by year
|       |-- api/apexClient.js         # Axios client
|       |-- hooks/
|       |   |-- useRaceData.js        # Races, laps, circuit path with fallback
|       |   `-- useCounterfactual.js  # Simulation hook
|       |-- pages/
|       |   |-- RewindPage.jsx        # Main race replay page
|       |   `-- ForecastPage.jsx      # Forecast page
|       `-- components/
|           |-- TrackCanvas/
|           |   |-- TrackCanvas.jsx
|           |   |-- trackUtils.js     # pointOnPath, colorForDriver, driverProgress
|           |   `-- useTrackAnimation.js  # Canvas render loop, car drawing
|           |-- Leaderboard/
|           |   `-- Leaderboard.jsx
|           |-- PlaybackControls/
|           |   `-- PlaybackControls.jsx
|           |-- WhatIfPanel/
|           |   `-- WhatIfPanel.jsx
|           |-- CircuitDNA/
|           |   `-- CircuitDNA.jsx
|           `-- ForecastDashboard/
|               `-- ForecastDashboard.jsx
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
`-- fia_pdfs/                         # FIA documents for Docling parsing
```

---

## 6. Database

### Provider
Supabase PostgreSQL, session pooler endpoint, SQLAlchemy URL format.

### Migration State
Alembic revision: `c254d08a60f5` — applied and verified.

### Tables
```text
circuits, drivers, constructors, seasons, races,
race_results, lap_times, pit_stops, safety_cars,
telemetry_paths, race_embeddings, scenarios
```

### Verified Row Counts (2026-05-09)

Full 2023 season ingested:

```text
seasons=1
circuits=22
drivers=22
constructors=10
races=22
race_results=440        (22 drivers × 20 races approximately)
lap_times=~23000        (full season)
pit_stops=~660          (full season)
safety_cars=0           (not yet ingested)
telemetry_paths=0       (not yet ingested)
race_embeddings=0       (pending Docling/RAG)
scenarios=0             (user-generated)
```

### Circuit GPS Paths

```text
circuits with gps_path: 1 (Bahrain International Circuit — 729 points)
circuits without gps_path: 21 (need FastF1 ingestion)
```

---

## 7. API Endpoints

All endpoints verified working against live Supabase data.

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/` | ✅ | Health check |
| GET | `/races` | ✅ | All 22 races |
| GET | `/races/{id}/laps` | ✅ | Full lap-by-lap data |
| GET | `/circuits/{id}/path` | ✅ | GPS path when available |
| GET | `/circuits/` | ✅ | All circuits |
| POST | `/counterfactual/simulate` | ✅ | Full deterministic engine |
| GET | `/forecast/{id}` | ⚠️ | Placeholder only |
| POST | `/scenarios` | ✅ | Saves what-if scenarios |
| GET | `/scenarios` | ✅ | Lists saved scenarios |

---

## 8. Counterfactual Engine

**File:** `backend/ai/counterfactual.py`

**Status:** Fully implemented and verified.

**Supported change types:**

| change_type | Effect |
|-------------|--------|
| `pit_lap` | Moves driver's pit stop to a different lap, applies average pit duration delta |
| `dnf` | Retires driver from specified lap |
| `fastest_lap` | Overrides a driver's lap time on a specific lap |

**How it works:**
1. Load all lap times and pit stops for the race into memory
2. Apply each change to a modified copy of the data
3. Recompute cumulative elapsed time per driver per lap
4. Re-rank drivers by cumulative time each lap
5. Return `alt_laps` in the same shape as `GET /races/{id}/laps`

**Verified output:** 200 OK, 95KB response for Bahrain 2023 with HAM pit_lap change, full 57 laps recomputed.

**Next step:** Pass actual vs alternate summary to Granite via IBM Bob for natural language explanation.

---

## 9. Frontend Visual System

### Team Color System

**File:** `frontend/src/teamColors.js`

- `TEAM_COLORS` — constructor ref → primary/accent hex
- `DRIVER_TEAM_2023` — driver code → constructor ref for 2023
- `DRIVER_TEAMS_BY_YEAR` — year → driver team map (extensible)
- `getDriverPrimary(code, year)` — single lookup used by canvas and leaderboard

**Adding a new season:** Add a `DRIVER_TEAM_20XX` object and entry in `DRIVER_TEAMS_BY_YEAR`.

### Canvas Renderer

**Files:** `useTrackAnimation.js`, `trackUtils.js`

- Track drawn as speed-gradient segments (blue=slow corners, red=fast straights)
- Uses real `speed` values from FastF1 GPS data stored in `circuits.gps_path`
- F1 car silhouette: body, cockpit, front wing, rear wing
- Car rotates to face direction of travel using `Math.atan2` between consecutive path points
- Ghost cars drawn at 35% opacity for counterfactual alternate positions
- Driver code label rendered below each car

### 2023 Team Colors Reference

| Team | Primary | Drivers |
|------|---------|---------|
| Red Bull | `#3671C6` | VER, PER |
| Ferrari | `#dc0000` | LEC, SAI |
| Mercedes | `#00d2be` | HAM, RUS |
| Aston Martin | `#006f62` | ALO, STR |
| McLaren | `#ff8700` | NOR, PIA |
| Alpine | `#0090ff` | OCO, GAS |
| AlphaTauri | `#1634cb` | TSU, DEV |
| Alfa Romeo | `#b12335` | BOT, ZHO |
| Haas | `#cccccc` | MAG, HUL |
| Williams | `#00a0dd` | ALB, SAR |

---

## 10. Known Issues and Technical Debt

### Visual Issues (deferred — being handled separately)
- Leaderboard shows 3-letter code in both tag and name columns (should show surname)
- Only 18 of 20 drivers visible in leaderboard
- What-If panel partially cut off at bottom of right column

### Functional Issues
- 21 circuits have no GPS path — need FastF1 ingestion run per circuit
- Tire compound data is null — not available from Jolpica
- Safety car periods not ingested
- Forecast endpoint returns placeholder only
- IBM Granite generation blocked pending IBM Bob integration

### Infrastructure
- No authentication
- No deployment pipeline
- No test suite
- `backend/%SystemDrive%/` artifact from failed process launch — gitignored, needs manual Windows cleanup

---

## 11. Immediate Next Steps

### Step 1 — IBM Bob Integration (Current Priority)
1. Sign up at `https://bob.ibm.com/trial`
2. Get Bob API endpoint and key
3. Update `backend/ai/granite.py` to use Bob endpoint
4. Test Granite generation call end to end
5. Wire explanation into counterfactual simulate response
6. Display in frontend sim note panel

### Step 2 — Ingest Remaining Circuit GPS Paths
Run for each remaining round:
```powershell
cd "D:\Projects\APEX-Racing Records\backend"
.\.venv\Scripts\python.exe -B ingestion/run_circuits.py --year 2023 --round 2
```
Repeat for rounds 2-22. Each downloads FastF1 session data and stores GPS path.

### Step 3 — IBM Docling Integration
1. Source FIA 2023 race regulation PDFs
2. Install and run Docling on PDF files
3. Chunk output text
4. Generate and store embeddings in `race_embeddings`
5. Build RAG retrieval in `backend/ai/rag.py`

### Step 4 — Forecast Baseline
1. Build heuristic model using: recent form, grid position, constructor pace, circuit type
2. Return real probability distribution from `GET /forecast/{race_id}`
3. Wire Granite explanation on top

### Step 5 — UI Polish
1. Fix leaderboard surname display
2. Fix 18 vs 20 driver count
3. Fix What-If panel overflow
4. Apply full redesign from mockup

### Step 6 — Deployment
1. Deploy frontend to Vercel
2. Deploy backend to Railway or Render
3. Database stays on Supabase

---

## 12. Startup Commands

**Backend:**
```powershell
cd "D:\Projects\APEX-Racing Records\backend"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend:**
```powershell
cd "D:\Projects\APEX-Racing Records\frontend"
npm run dev
```

**Ingest a circuit GPS path:**
```powershell
cd "D:\Projects\APEX-Racing Records\backend"
.\.venv\Scripts\python.exe -B ingestion/run_circuits.py --year 2023 --round 1
```

**Ingest a race (single round):**
```powershell
.\.venv\Scripts\python.exe -B -m ingestion.run_all --year 2023 --round 1
```

---

## 13. Critique Questions for Other AI Models

1. Is the counterfactual pit_lap delta calculation accurate — should average pit duration be used or driver-specific?
2. What is the correct way to handle lapped drivers in position recomputation?
3. Should circuit GPS paths be versioned per season or shared across seasons for the same circuit?
4. What is the minimum RAG chunk size for FIA regulation documents to be useful for Granite?
5. How should the forecast model handle driver DNF probability without historical reliability data?
6. What tables are missing for accurate tire strategy simulation?
7. Should `gap_to_leader_ms` be stored or derived on every request?
8. What is the right boundary between deterministic counterfactual logic and Granite generation?
9. How should IBM Bob credentials be rotated after the 30-day trial?
10. What test coverage is needed before the counterfactual engine can be trusted for demo use?