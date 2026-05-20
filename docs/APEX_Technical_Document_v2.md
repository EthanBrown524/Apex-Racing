# APEX Race Director - Technical Document (v2)

**Project name:** APEX Race Director
**Tagline:** An AI-powered Formula 1 alternate-history simulator built on the IBM watsonx + Granite stack.
**Status:** Hackathon build, May 2026. Backend and frontend integrated, all six 2019-2024 seasons supported by the ingestion pipeline.

---

## 1. Product summary

APEX turns every Grand Prix from 2019-2024 into an editable timeline. Three modes:

| Mode | Path | What it does |
|------|------|--------------|
| **Library** | `/` | Grid of every race grouped by season, click to open. |
| **Time Machine** | `/rewind/:raceId` | Replay a race with telemetry-driven car positions, live leaderboard, AI commentary that updates lap-by-lap, and a free-form "Ask APEX" panel. |
| **What-If Lab** | `/rewind/:raceId` (right rail) | Apply strategy changes (pit lap, DNF, weather, safety car, mechanical, grid swap, fastest lap). The deterministic simulator recomputes the standings; Granite explains the new outcome with citations. |
| **Glory Path** | `/glory/:raceId` | Pick a driver + target finish position. APEX greedy-searches the smallest set of changes that gets them there and Granite narrates the alternate storyline. |
| **Forecast** | `/forecast/:raceId` | Win-probability + circuit-DNA radar derived from historical aggregates. |

The whole UI runs against a single FastAPI service; the frontend never calls IBM endpoints directly.

---

## 2. Architecture

```
+------------------+     +----------------+     +---------------------+
|  React (Vite)    | --> |  FastAPI       | --> |  PostgreSQL +       |
|  ports 5173      |     |  port 8000     |     |  pgvector           |
+------------------+     +----------------+     +---------------------+
                                |   |
                                |   +--> watsonx.ai
                                |        - Granite-3-8b-instruct  (chat / explain)
                                |        - slate-30m-english-rtrvr (embeddings)
                                |
                                +--> Docling (FIA stewards' PDFs -> RAG chunks)
                                +--> Langflow (visual flow graphs, exportable JSON)
                                +--> FastF1 + Ergast (data ingestion)
```

### Backend layout

```
backend/
  main.py                 FastAPI app; registers all routers; lifespan disposes engine
  api/
    races.py              GET /races, GET /races/{id}/laps, GET /races/{id}/telemetry/{lap}
    circuits.py           GET /circuits, GET /circuits/{id}/path
    counterfactual.py     POST /counterfactual/simulate
    forecast.py           GET /forecast/{race_id}
    scenarios.py          POST /scenarios, GET /scenarios
    glory_path.py         POST /glory-path/solve           <-- new
    commentary.py         GET /ai/commentary/{race_id}, POST /ai/ask  <-- new
  ai/
    granite.py            watsonx.ai text-generation client (55-min token cache)
    embeddings.py         watsonx.ai embedding client; hash-vector fallback when offline
    rag.py                pgvector retrieve + upsert; race_id-scoped top-k
    counterfactual.py     deterministic engine + Granite explanation
                          change types: pit_lap, dnf, fastest_lap, mechanical,
                                        weather, safety_car, grid_swap
    glory_path.py         greedy search over candidate interventions
    commentary.py         narrative + free-form Q&A with RAG citations
    forecast.py           historical-form heuristic + circuit-DNA aggregation
  ingestion/
    ergast.py             metadata + results + lap times + pit stops, paginated
    fastf1_loader.py      circuit GPS outlines from FastF1
    run_telemetry.py      per-driver per-lap x/y/speed paths
    fia_parser.py         Docling -> RAG (FIA stewards' decisions, race control logs)
    embed_races.py        synthesizes race-summary chunks and embeds them
    run_bulk.py           orchestrates 2019-2024 across all four phases
  db/
    connection.py         SQLAlchemy engine + SessionLocal + get_db()
    models.py             11 ORM models; pgvector Vector(1536) for race_embeddings
    migrations/           Alembic; initial schema + gps_image addition
```

### Frontend layout

```
frontend/src/
  App.jsx                 Router shell with topbar nav (Library / Time Machine / Glory Path / Forecast / About)
  styles.css              Single global stylesheet, broadcast-grade dark theme
  teamColors.js           Team -> color map for 2019-2024, per-driver lookup
  api/apexClient.js       Axios wrapper for every backend endpoint
  hooks/
    useRaceData.js        races + circuit path + lap data, with per-race cache
    useTelemetry.js       per-lap telemetry prefetch
    useCounterfactual.js  POST /counterfactual/simulate
    useGloryPath.js       POST /glory-path/solve
    useCommentary.js      GET /ai/commentary/{id}
    useAIChat.js          stateful conversation against POST /ai/ask
  pages/
    LibraryPage.jsx       race grid filtered by season + search
    RewindPage.jsx        TrackCanvas + Leaderboard + WhatIfPanel|AIChatBox + AINarrator
    GloryPathPage.jsx     glory-path form + result hero + step list + citations
    ForecastPage.jsx      win % bars + circuit-DNA radar + risks
    AboutPage.jsx         project + IBM-stack feature cards
  components/
    TrackCanvas/          telemetry-driven car renderer (preserved from v1)
    Leaderboard/          team-coloured position list, tire compound badges
    WhatIfPanel/          extended to 7 change types
    PlaybackControls/     play / pause / speed / lap scrubber
    CircuitDNA/           radar chart + 2x2 trait table
    ForecastDashboard/    relative win-% bar list
    AINarrator/           Granite-narrated commentary panel
    AIChatBox/            free-form Q&A with citations
    Citations/            [n] source chips with hover preview
```

---

## 3. Data model

All eleven tables live in PostgreSQL; the `race_embeddings.embedding` column is `Vector(1536)` when pgvector is installed, otherwise the SQLAlchemy `TypeDecorator` falls back to Text.

```
circuits        (id, name, location, country, length_km, gps_path JSONB, gps_image TEXT)
drivers         (id, driver_ref unique, code, forename, surname, nationality)
constructors    (id, constructor_ref unique, name, nationality)
seasons         (year PK)
races           (id, season_year FK, round, circuit_id FK, name, date, total_laps)
race_results    (id, race_id, driver_id, constructor_id, grid_position, final_position, points, status)
lap_times       (id, race_id, driver_id, lap, position, time_ms, gap_to_leader_ms)
pit_stops       (id, race_id, driver_id, stop_number, lap, duration_ms, tire_in, tire_out)
safety_cars     (id, race_id, type, lap_start, lap_end)
telemetry_paths (id, race_id, driver_id, lap, path JSONB [{x,y,t_ms,speed}])
race_embeddings (id, race_id, content TEXT, embedding Vector(1536), metadata JSONB)
scenarios       (id, label, race_id, changes JSONB, created_at)
```

### Indexes that matter

- `lap_times (race_id, lap, position)` - leaderboard + counterfactual reads
- `race_embeddings USING ivfflat (embedding vector_cosine_ops)` - install with `CREATE INDEX ON race_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);` once embeddings exceed ~50k rows
- Unique constraints on `(race_id, driver_id, lap)` for lap_times and telemetry_paths prevent duplicate ingestion

---

## 4. IBM stack usage

### 4.1 Granite-3-8b-instruct (watsonx.ai text generation)

- Counterfactual explanations (`ai/counterfactual.py:_build_granite_prompt`)
- Glory Path storyline (`ai/glory_path.py:find_glory_path`)
- Live commentary (`ai/commentary.py:narrate_race`)
- Free-form Q&A (`ai/commentary.py:answer_question`)

Token cache lives in `ai/granite.py`; the OAuth token is fetched from IBM IAM and reused for 55 minutes.

All prompts:
1. State the role ("expert F1 race analyst").
2. Provide *only* the verified facts (race name, top-5, summary).
3. Include the retrieved chunks.
4. Tell Granite to cite by `[n]` and not invent positions.

### 4.2 Slate-30m-english-rtrvr (watsonx.ai embeddings)

- `ai/embeddings.py:embed_texts` produces the query vector and the chunk vectors.
- Stored padded/trimmed to 1536 dim to match the existing `RaceEmbedding.embedding` column.
- Hash-trigram fallback (`_hash_embed`) keeps the RAG path functional when IBM credentials are missing - the demo never breaks.

### 4.3 Docling

- `ingestion/fia_parser.py` uses `docling.document_converter.DocumentConverter().convert(...)` to lift markdown out of FIA stewards' PDFs.
- The markdown is chunked through `ai.rag.chunk_for_storage` (800-char window, 120-char overlap) and embedded.
- Source tag `fia_decision` flows through citations so the frontend chip reads `[3] fia_decision`.

### 4.4 Langflow

Three exportable flow JSONs in `langflow/`:

- `counterfactual_flow.json` - Race+Changes -> Embedder -> PGVector -> Simulate -> Prompt -> Granite -> Output
- `glory_path_flow.json` - Glory request -> Candidates -> Greedy loop (with simulate-step feedback) -> RAG -> Storyline prompt -> Granite -> Output
- `forecast_flow.json` - Race ID -> Recent results + Circuit DNA -> win% heuristic + risk text -> Output

The JSON is hand-authored to match Langflow's node/edge schema and visually reproduces the actual pipeline; import via Langflow's "Upload Flow" button to inspect or extend.

---

## 5. Counterfactual engine

Located in `ai/counterfactual.py`. Loads every lap-time row for the race, copies them into memory, applies each change, then recomputes cumulative time + per-lap ranks.

### Change types

| `change_type` | Driver | Lap | Value | Effect |
|---------------|--------|-----|-------|--------|
| `pit_lap`     | required | (orig pit lap) | new pit lap | Removes the historical pit penalty, applies it on the new lap |
| `dnf`         | required | retirement lap | unused | Drops all laps from `lap` onwards |
| `fastest_lap` | required | target lap | new time_ms | Rewrites a single lap's time_ms |
| `mechanical`  | required | start lap | ms penalty/lap (default 800) | Adds a recurring penalty from lap N onwards |
| `weather`     | unused | start lap | `{ benefits: ["VER","HAM"], penalty_ms: 1200 }` | Applies global penalty except to listed drivers |
| `safety_car`  | unused | unused | start lap | Refunds ~12s to anyone pitting in lap range `[start, start+3]` |
| `grid_swap`   | required | switch lap | partner driver code | Swaps a constant delta until lap N |

### Output

```json
{
  "race_id": 12,
  "alt_laps": [{"lap": 1, "drivers": [...]}, ...],
  "changes": [...],
  "summary": ["HAM pit moved to lap 18", ...],
  "explanation": "Granite-generated 3-4 sentence narrative.",
  "citations": [{"index": 1, "source": "race_narrative", "snippet": "..."}],
  "actual_top5": ["VER", "PER", "ALO", "RUS", "SAI"],
  "alt_top5":    ["VER", "HAM", "PER", "ALO", "RUS"]
}
```

---

## 6. Glory Path search

`ai/glory_path.py:find_glory_path` performs three steps:

1. **Candidate surface.** Scans the actual race for high-leverage interventions:
   - slow pit stops (>15% above the driver's average) -> move earlier by 3 laps
   - drivers currently ahead of the target driver -> introduce a `dnf`
   - the driver's worst stint lap -> rewrite to 93% of that time
2. **Greedy loop.** Try each candidate in order. Accept it iff the target driver's final position improves by ≥1. Halt on three terminals: target reached, MAX_CHANGES=4 applied, or two no-gain iterations in a row.
3. **Granite storyline.** Combine accepted changes + retrieved race context (`RAG retrieve` over `{driver_code} race story strategy mistakes safety car incidents`). Granite writes 3-5 sentences citing chunks.

Returns starting position, achieved position, applied changes with rationale strings, the Granite storyline, and citation chips.

---

## 7. Ingestion pipeline (2019-2024)

```
python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024
```

Per-year phases:

1. **Ergast** - drivers, constructors, races, results, lap times, pit stops. Restart-safe; skips rounds where results+laps+pits already exist.
2. **FastF1 circuit paths** - one path per circuit, idempotent (`Circuit.gps_path` is null-checked).
3. **Telemetry sampling** - 10 evenly-spaced laps per race by default (full ingest with `--skip-telemetry` removed and a wider lap list).
4. **Embeddings** - synthesizes 4 chunks per race (result, pit windows, safety cars, lead changes) and embeds via watsonx.

FIA stewards' decisions are ingested independently:
```
python -m ingestion.fia_parser path/to/decision.pdf --race-id 42
python -m ingestion.fia_parser /path/to/decisions_dir
```

---

## 8. API contract (consumer view)

| Method | Path | Body / Query | Returns |
|--------|------|--------------|---------|
| GET | `/` | - | `{ status: "ok" }` |
| GET | `/races` | - | `[{ id, name, season, round, circuit_id, circuit_name, date, total_laps }]` |
| GET | `/races/{id}/laps` | - | `{ race_id, laps: [{ lap, drivers: [{ driver_id, code, position, gap_ms, time_ms, tire, in_pit }] }] }` |
| GET | `/races/{id}/telemetry/{lap}` | - | `{ race_id, lap, drivers: [{ code, path: [{x,y,t_ms,speed}] }] }` |
| GET | `/circuits` | - | `[{ id, name, location, country, has_path }]` |
| GET | `/circuits/{id}/path` | - | `{ circuit_id, name, path: [{x,y,distance_pct,speed}] }` |
| POST | `/counterfactual/simulate` | `{ race_id, changes: [{ driver_code, change_type, lap, value }] }` | `{ alt_laps, summary, explanation, citations, actual_top5, alt_top5 }` |
| POST | `/glory-path/solve` | `{ race_id, driver_code, target_position }` | `{ starting_position, achieved_position, applied, rationales, explanation, citations }` |
| GET | `/ai/commentary/{id}?up_to_lap=N` | - | `{ race_id, up_to_lap, narrative, citations }` |
| POST | `/ai/ask` | `{ race_id, question }` | `{ race_id, question, answer, citations }` |
| GET | `/forecast/{id}` | - | `{ race_id, predictions, circuit_dna, risk_factors }` |
| POST | `/scenarios` | `{ label, race_id, changes }` | `{ scenario_id }` |
| GET | `/scenarios` | - | `[{ scenario_id, label, race_id, changes, created_at }]` |

---

## 9. Environment

Required:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/apex
FRONTEND_URL=http://localhost:5173
```

Optional (everything still runs without these - Granite paths return the deterministic-fallback explanation):
```
IBM_API_KEY=...
WATSONX_PROJECT_ID=...
WATSONX_URL=https://us-south.ml.cloud.ibm.com
DB_POOL_SIZE=4
DB_MAX_OVERFLOW=0
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

---

## 10. Demo script (2-minute pitch)

1. **Library** -> click "2023 Monaco Grand Prix".
2. **Time Machine** opens. AI narrator panel says "Through lap 12, Verstappen leads from pole..." with [1] [2] chips.
3. Switch right rail to **What-If**: pick `HAM`, `pit_lap`, lap 32, value 28. Click Simulate.
4. New leaderboard appears with HAM up two places; Granite explains why.
5. Switch right rail to **Ask APEX**: type "what happened to PER?". Granite answers with citations.
6. Navigate to **Glory Path**. Driver: `ALO`, target: P1. Click Find Glory Path. Watch the hero "P7 -> P1" with three interventions and a storyline.
7. Wrap on **About**: show the IBM stack feature cards.
