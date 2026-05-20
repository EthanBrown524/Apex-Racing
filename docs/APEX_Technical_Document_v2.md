# APEX Race Director - Technical Document (v2)

**Project name:** APEX Race Director
**Tagline:** An AI-powered Formula 1 alternate-history simulator built on the IBM watsonx + Granite stack.
**Status:** Hackathon build, May 2026. Backend and frontend integrated, all six 2019-2024 seasons supported by the ingestion pipeline.

---

## 1. Product summary

APEX turns every Grand Prix from 2019-2024 into an editable timeline. Nine routes:

| Page | Path | What it does |
|------|------|--------------|
| **Home** | `/` | Marketing landing page - hero with bold typography, animated scale strip, three pillars (Time Machine / What-If / Glory Path), an "AI in F1" narrative section, featured scenarios row, IBM stack cards, final CTA. |
| **Seasons** | `/seasons` | Six rich year cards - 2019..2024 - with champion, tagline, narrative, iconic moment, and per-season ingestion progress bar. Primary year-selection surface. |
| **Library** | `/library`, `/seasons/:year` | Race grid filtered by year + free-text search. Year-scoped view shows season narrative as the hero. |
| **Showcase** | `/showcase` | Pre-baked demo scenarios (Abu Dhabi 2021, Monaco 2022, Brazil 2022, Singapore 2023, Glory Path: Alonso, Glory Path: Leclerc). One-click launch into the relevant mode. |
| **Time Machine** | `/rewind/:raceId` | Replay a race with telemetry-driven car positions, live leaderboard, lap-by-lap AI commentary, free-form "Ask APEX", and keyboard shortcuts. |
| **What-If Lab** | right rail of `/rewind/:raceId` | Apply strategy changes (7 types). Deterministic simulator recomputes standings; Granite explains with citations; Realism chip + Championship Impact card. |
| **Glory Path** | `/glory/:raceId` | Pick a driver + target position. Greedy search finds minimum interventions; Granite narrates with citations; animated P-countdown hero. |
| **Forecast** | `/forecast/:raceId` | Win-probability bars + circuit-DNA radar. |
| **Stats** | `/stats` | Scale showcase - animated big-number heroes, per-season progress bars, IBM stack panel. |
| **About** | `/about` | Stack overview + glossary tooltips + scale strip. |

The whole UI runs against a single FastAPI service; the frontend never calls IBM endpoints directly. A `Footer` component fetches `/health` and surfaces live diagnostics (ingested race count, Granite status, pgvector status).

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
  requirements.txt
  alembic.ini
  api/
    races.py              GET /races, GET /races/{id}/laps, GET /races/{id}/telemetry/{lap}
    circuits.py           GET /circuits, GET /circuits/{id}/path
    counterfactual.py     POST /counterfactual/simulate, POST /counterfactual/realism
    forecast.py           GET /forecast/{race_id}
    scenarios.py          POST /scenarios, GET /scenarios
    glory_path.py         POST /glory-path/solve
    commentary.py         GET /ai/commentary/{race_id}, POST /ai/ask
    championship.py       POST /championship/impact
    showcase.py           GET /showcase, GET /showcase/{scenario_id}
    health.py             GET /health (counts + Granite status + pgvector status)
    stats.py              GET /stats (headline numbers + per-season progress
                          + embedding source breakdown - drives /stats page)
  ai/
    granite.py            watsonx.ai text-generation client (55-min token cache)
    embeddings.py         watsonx.ai embedding client; hash-vector fallback when offline
    rag.py                pgvector retrieve + upsert; race_id-scoped top-k
    changes.py            shared constants + describe_change() + safe_int()
    counterfactual.py     deterministic engine + Granite explanation; 7 change types
    glory_path.py         greedy search over candidate interventions
    commentary.py         narrative + free-form Q&A with RAG citations
    forecast.py           historical-form heuristic + circuit-DNA aggregation
    championship.py       end-of-season standings recompute under counterfactual
    realism.py            Granite-judged 0-1 score with heuristic fallback
    showcase_scenarios.py curated demo scenarios (Abu Dhabi 2021 etc.)
  tests/                  pytest smoke tests (18 passing) - no DB or IBM required
  ingestion/
    ergast.py             metadata + results + lap times + pit stops, paginated
    fastf1_loader.py      circuit GPS outlines from FastF1
    run_telemetry.py      per-driver per-lap x/y/speed paths
    fia_parser.py         Docling -> RAG (FIA stewards' decisions, race control logs)
    embed_races.py        synthesizes race-summary chunks and embeds them
    run_bulk.py           orchestrates 2019-2024 across all four phases;
                          tqdm progress bars, per-year summary, --parallel-years
    status.py             CLI - print ingestion progress per season as bars
    export.py             dump the DB to JSON for backup/portability
    _normalize.py         x/y point normalization helper (was backend/utils/)
  db/
    connection.py         SQLAlchemy engine + SessionLocal + get_db()
    models.py             11 ORM models; pgvector Vector(1536) for race_embeddings
    migrations/           Alembic; initial schema + gps_image addition
```

### Frontend layout

```
frontend/src/
  main.jsx                React entry; imports styles/index.css and renders <App/>
  App.jsx                 Router shell with topbar nav (Library / Time Machine / Glory Path / Forecast / About)
  api/
    apexClient.js         Axios wrapper for every backend endpoint
  data/                   Static data + fallbacks (no React, no logic)
    sampleData.js         Offline fallback - 28 sample races across 6 seasons + sampleStats
    teamColors.js         Team -> color map for 2019-2024, per-driver lookup
    seasons.js            Year metadata (champion, tagline, narrative,
                          iconic moment, accent colour) for the Seasons page
  styles/                 Single-theme CSS split by concern; index.css imports the rest
    index.css             Entry point - just @imports the four below in order
    base.css              :root design tokens, reset, typography, keyframes
    layout.css            App shell, topbar, nav, page grids, race bar, responsive
    components.css        Buttons, forms, leaderboard, track HUD, what-if, citations, ai chat
    pages.css             Library grid, Glory hero, Forecast layout, About hero
    home.css              Home + Seasons landing pages (hero, pillars, narrative beats, year cards)
    stats.css             Stats page + StatStrip
    extras.css            ChampionshipImpact, RealismChip, Showcase, Skeleton, Footer, Glossary, KeyboardHints
  hooks/
    useRaceData.js        races + circuit path + lap data, with per-race cache
    useTelemetry.js       per-lap telemetry prefetch
    useCounterfactual.js  POST /counterfactual/simulate
    useGloryPath.js       POST /glory-path/solve
    useCommentary.js      GET /ai/commentary/{id}
    useAIChat.js          stateful conversation against POST /ai/ask
  pages/
    HomePage.jsx          landing page - hero, scale strip, three pillars,
                          AI-in-F1 narrative beats, featured scenarios, IBM
                          stack cards, final CTA
    SeasonsPage.jsx       year selection grid - rich cards per season with
                          champion + tagline + narrative + iconic moment +
                          ingestion progress bar
    LibraryPage.jsx       race grid; accepts /:year to scope; shows the season
                          narrative as hero when scoped; skeleton loaders; scale strip
    StatsPage.jsx         scale showcase - animated big numbers + season bars + IBM stack panel
    ShowcasePage.jsx      curated demo cards; one-click launch with pre-filled changes
    RewindPage.jsx        TrackCanvas + Leaderboard + WhatIfPanel|AIChatBox + AINarrator
                          + ChampionshipImpact + RealismChip + keyboard shortcuts
    GloryPathPage.jsx     animated P-start->P-achieved hero + step list + citations
    ForecastPage.jsx      win % bars + circuit-DNA radar + risks
    AboutPage.jsx         project + IBM-stack feature cards + glossary tooltips
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
    ChampionshipImpact/   season-standings recompute card with title-flip badge
    RealismChip/          0-1 score chip with Plausible/Borderline/Stretch/Fantasy
    Skeleton/             SkeletonRow + SkeletonCard + SkeletonList
    Footer/               diagnostics-bound IBM-stack chip row
    Glossary/             F1-jargon hover-tooltip term wrapper
    KeyboardHints/        small Space/arrows/R legend under the track
    StatHero/             animated count-up number + label; StatStrip wraps N
```

  hooks/
    useStats.js           fetches /stats, falls back to sampleStats
    useCountUp.js         eased count-up animation hook + formatLargeNumber
    ...existing hooks unchanged

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

### Performance notes

- `_recompute_positions` pre-indexes each driver's laps by lap number, turning
  the per-lap scan from O(len(driver_laps)) to O(1) per driver. For a 70-lap
  race with 20 drivers that's ~28k fewer comparisons.
- `_circuit_dna` runs three `SELECT COUNT(...)` round-trips instead of
  materializing every row and calling `len()` client-side. One historical
  query per stat, not one per race.
- `ai/changes.py` centralizes `describe_change()` and `safe_int()` so the
  counterfactual engine and Glory Path narrator can't drift out of sync.

---

## 5b. Championship Impact

`ai/championship.py:compute_championship_impact` recomputes end-of-season
standings under a counterfactual race result, assuming every other race is
unchanged.

1. Pull actual `RaceResult.points` totals per driver + constructor for the season.
2. Simulate the counterfactual at the target race; derive alternate points
   from the alternate finishing positions using F1's 25/18/15/12/10/8/6/4/2/1
   table.
3. Apply the delta to the season totals.
4. Compare leaders: if the alternate champion differs from the actual one,
   the response carries `championship_changed: true` and the UI shows a
   "TITLE CHANGES" badge.

This is the "Hamilton would have won 2021 by 12 points" moment. The card
also lists the top three biggest movers (`HAM +18pts, VER -25pts, ...`)
and a one-paragraph narrative explaining the swing.

## 5c. Realism Score

`ai/realism.py:score_counterfactual` returns a 0..1 score + label
(Plausible / Borderline / Stretch / Fantasy).

- **Heuristic baseline**: 1.0 minus a fixed cost per change (weather and
  safety_car are most expensive, fastest_lap and DNF are cheap).
- **Granite refinement**: a short SCORE/REASON prompt asks Granite to rate
  the scenario; result blended 70/30 with the heuristic. Falls back silently
  to the heuristic when credentials are missing.

The chip renders next to the Granite explanation in the What-If Lab so the
judge sees instant credibility feedback.

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
python -m ingestion.run_bulk --years 2019 2020 --parallel-years 2   # 2 seasons concurrently
python -m ingestion.run_bulk --years 2024 --full-telemetry          # every lap (slow)
python -m ingestion.status                                          # progress bars
python -m ingestion.export --out apex_dump.json                     # backup
```

Per-year phases:

1. **Ergast** - drivers, constructors, races, results, lap times, pit stops. Restart-safe; skips rounds where results+laps+pits already exist.
2. **FastF1 circuit paths** - one path per circuit, idempotent (`Circuit.gps_path` is null-checked).
3. **Telemetry sampling** - 10 evenly-spaced laps per race by default (`--full-telemetry` ingests every lap).
4. **Embeddings** - synthesizes 4 chunks per race (result, pit windows, safety cars, lead changes) and embeds via watsonx.

`run_bulk.py` shows tqdm progress bars per phase and prints a totals table at
the end (races / laps / pits / telemetry / embeddings counts and elapsed time).
`--parallel-years N` runs N seasons concurrently via multiprocessing.

`status.py` prints a current-state bar chart per season - useful for "did my
overnight job finish?" and for screenshots in the demo.

`export.py` dumps the entire DB to JSON so you can ingest once on a beefy
machine and ship the dump to the demo laptop, skipping the slow FastF1 phase
on demo day.

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
| GET | `/health` | - | `{ status, counts, seasons, pgvector_installed, granite_configured, embedding_sources, ingestion_complete }` |
| GET | `/stats` | - | `{ headline, drivers, constructors, circuits, embeddings, season_breakdown, embedding_sources, years_target, total_expected_races, overall_progress }` |
| GET | `/races` | - | `[{ id, name, season, round, circuit_id, circuit_name, date, total_laps }]` |
| GET | `/races/{id}/laps` | - | `{ race_id, laps: [{ lap, drivers: [{ driver_id, code, position, gap_ms, time_ms, tire, in_pit }] }] }` |
| GET | `/races/{id}/telemetry/{lap}` | - | `{ race_id, lap, drivers: [{ code, path: [{x,y,t_ms,speed}] }] }` |
| GET | `/circuits` | - | `[{ id, name, location, country, has_path }]` |
| GET | `/circuits/{id}/path` | - | `{ circuit_id, name, path: [{x,y,distance_pct,speed}] }` |
| POST | `/counterfactual/simulate` | `{ race_id, changes: [{ driver_code, change_type, lap, value }] }` | `{ alt_laps, summary, explanation, citations, actual_top5, alt_top5 }` |
| POST | `/counterfactual/realism` | `{ race_id, changes }` | `{ score, label, reasoning, source }` |
| POST | `/championship/impact` | `{ race_id, changes }` | `{ season, actual_champion, alternate_champion, championship_changed, actual_standings, alternate_standings, biggest_movers, narrative }` |
| POST | `/glory-path/solve` | `{ race_id, driver_code, target_position }` | `{ starting_position, achieved_position, applied, rationales, explanation, citations }` |
| GET | `/ai/commentary/{id}?up_to_lap=N` | - | `{ race_id, up_to_lap, narrative, citations }` |
| POST | `/ai/ask` | `{ race_id, question }` | `{ race_id, question, answer, citations }` |
| GET | `/forecast/{id}` | - | `{ race_id, predictions, circuit_dna, risk_factors }` |
| GET | `/showcase` | - | `[{ id, title, subtitle, season, round, mode, tagline, race_id, ... }]` |
| GET | `/showcase/{id}` | - | one resolved scenario |
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

1. **Land on /** — Home page. Hero says "Rewrite Formula 1. Powered by IBM
   Granite." Scale strip shows the live count of races/laps/pit stops/data
   points. Scroll past the three pillars and the AI-in-F1 narrative.
2. Click **Browse seasons**. Six rich year cards: 2019..2024, each with
   champion, tagline, narrative, and an ingestion progress bar.
3. Click **2021**. Library scoped to that year - hero reads "The closest
   title fight of the century" with the season narrative.
4. (Or jump straight from Home to **Showcase** -> "Abu Dhabi 2021 - the
   title-deciding lap" for the headline demo.)
5. The race opens with the change already staged. Hit **Simulate**.
6. Granite explanation appears with citations and a **Realism chip**
   ("Realism 73% Plausible").
7. Click **Show championship impact**. Card flips with "TITLE CHANGES" - the
   alternate champion, biggest movers, narrative.
8. Switch right rail to **Ask APEX**: "what happened to PER?". Granite
   answers with [1] [2] citations.
9. Navigate to **Glory Path** -> Alonso back to the top step. Animated
   `P7 -> P1` countdown.
10. Finish on **Stats**: the scale numbers count up live. Point at the Footer
    chips for the IBM-stack diagnostics.

## 11. Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

18 smoke tests cover:
- `safe_int`, `describe_change`, `strip_internal` (shared helpers)
- `_apply_changes` and `_recompute_positions` against a hand-built baseline
- Realism heuristic (no Granite required)
- Showcase scenario schema (no DB required)

None of these need Postgres or watsonx credentials - they run on a fresh
checkout in under a second.
