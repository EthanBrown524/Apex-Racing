# APEX Agent Briefing - Read This First

**Audience:** Any AI agent (Claude Sonnet/Haiku, GPT, etc.) joining this project mid-stream.
**Purpose:** Bring you to full context in 5 minutes so you can do useful work without re-reading every file.

This is a self-contained briefing. The repo also contains four longer docs - pull
them when you need depth:

| Doc | When to read |
|-----|--------------|
| `docs/APEX_Technical_Document_v2.md` | Full architecture, data model, every API endpoint, demo script |
| `docs/SETUP_AND_INGEST.md` | Local Postgres setup + ingestion runbook (Windows + Bash) |
| `docs/SUPABASE_RUNBOOK.md` | Same, but for Supabase backends |
| `docs/ROADMAP_FOR_CLAUDE.md` | The waved task list for follow-on work (Wave 1-6) |

---

## 1. Mission - what APEX is

**APEX Race Director** is an AI-powered Formula 1 alternate-history simulator.
It indexes every Grand Prix from **2019-2024** (laps, pit stops, telemetry,
safety cars, FIA decisions) and lets a user:

- **Replay** any race with telemetry-driven cars on the real circuit, plus
  Granite-narrated commentary that updates lap by lap.
- **Run "what-if" scenarios** (7 change types: pit_lap, dnf, fastest_lap,
  mechanical, weather, safety_car, grid_swap). The engine recomputes the
  standings deterministically; Granite explains the new outcome with
  citations; a Realism chip rates plausibility; a Championship Impact card
  recomputes the season standings.
- **Solve Glory Paths** - "what's the smallest set of changes that gets HAM
  to P1 at Abu Dhabi 2021?". A greedy optimizer searches the candidate
  interventions; Granite narrates the resulting alternate storyline.
- **Forecast** upcoming races from historical aggregates.
- **Browse and discover** via Home / Seasons / Library / Showcase pages.

Built for the **IBM May 2026 hackathon**. The IBM stack is central:
**Granite-3-8b-instruct** for reasoning, **Slate-30m-english-rtrvr** for
embeddings, **Docling** for FIA PDF extraction, **Langflow** for flow
documentation.

---

## 2. Repository layout

```
testFork/
  README.md                       hackathon-facing front page
  .env.example                    DATABASE_URL, IBM_API_KEY, WATSONX_*
  .gitignore                      .env, .venv, node_modules, dist, fia_pdfs, etc

  backend/
    main.py                       FastAPI app; registers 11 routers; lifespan disposes engine
    requirements.txt              fastapi, sqlalchemy, fastf1, httpx, pgvector, docling, tqdm, pytest
    alembic.ini                   Alembic config
    api/                          one file per router
      races.py, circuits.py, counterfactual.py, forecast.py, scenarios.py,
      glory_path.py, commentary.py, championship.py, showcase.py, health.py, stats.py
    ai/                           all the intelligence lives here
      granite.py                  watsonx.ai text-generation client (55-min token cache)
      embeddings.py               watsonx.ai embeddings client + hash-vector fallback
      rag.py                      pgvector retrieve + upsert; race_id-scoped top-k
      changes.py                  shared describe_change(), safe_int(), strip_internal()
                                  + change-type constants. NEVER duplicate these.
      counterfactual.py           deterministic engine + Granite explanation. Pre-indexes
                                  laps in _recompute_positions for O(N+M). Takes an
                                  optional ai_director=True flag that invokes the Race
                                  Director pipeline before the engine runs.
      glory_path.py               greedy search over candidate interventions
      commentary.py               narrate_race + answer_question
      forecast.py                 historical-form heuristic + circuit-DNA aggregation
      championship.py             end-of-season standings recompute under counterfactual
      realism.py                  Granite-judged 0..1 score with heuristic fallback
      showcase_scenarios.py       6 curated demo scenarios (Abu Dhabi 2021 etc.)
      driver_profiles.py          5-axis skill ratings per driver derived from history.
                                  build_profiles_for_race(race_id) -> {code: {...}}.
                                  Defaults to 0.5 across the board when no history.
      race_director.py            Granite planner. Takes triggers (weather, safety_car,
                                  mechanical, dnf) + driver profiles, returns validated
                                  JSON of strategic decisions. JSON extraction tolerates
                                  preamble, code fences, garbage; schema validation
                                  drops unknown drivers/actions, clamps confidence.
      change_expander.py          Maps Race Director decisions (pit/retire/push/manage/
                                  stay_out) to engine change records (pit_lap, dnf,
                                  fastest_lap, mechanical).
    ingestion/                    CLI scripts run with `python -m ingestion.<name>`
      ergast.py                   metadata + results + lap times + pit stops, paginated
      fastf1_loader.py            circuit GPS outlines from FastF1
      run_telemetry.py            per-driver per-lap x/y/speed paths
      fia_parser.py               Docling -> RAG (FIA decision PDFs)
      embed_races.py              synthesize 4 chunks per race -> RAG index
      run_bulk.py                 orchestrates 2019-2024; tqdm progress, --parallel-years
      status.py                   CLI - prints ingestion progress per season as bars
      export.py                   CLI - dump DB to JSON
      _normalize.py               x/y normalization helper (private to ingestion/)
    db/
      connection.py               SQLAlchemy engine + SessionLocal + get_db()
      models.py                   11 ORM models; pgvector Vector(1536) for embeddings
      migrations/                 Alembic (do NOT touch manually)
    tests/                        48 pytest smoke tests. No DB or IBM keys required.

  frontend/
    package.json                  react 18, vite, axios, recharts, react-router-dom
    src/
      main.jsx                    React entry; imports styles/index.css
      App.jsx                     Router shell with topbar and 11 routes
      api/apexClient.js           Axios wrapper for every backend endpoint
      data/                       Static data only - NO React, NO logic
        sampleData.js             Offline fallback: 28 sample races across 6 seasons
        teamColors.js             Team -> color map for every driver 2019-2024
        seasons.js                Champion/tagline/narrative/icon for each season
      styles/                     Single-theme CSS, split by concern
        index.css                 @import entry point - do NOT create another styles.css
        base.css                  :root tokens, reset, keyframes
        layout.css                shell, topbar, page grids, race bar
        components.css            buttons, leaderboard, what-if, citations, chat, narrator
        pages.css                 library grid, glory hero, forecast layout, about hero
        home.css                  Home + Seasons landing styling
        stats.css                 Stats page + StatStrip animated heroes
        extras.css                ChampionshipImpact, RealismChip, Showcase, Skeleton, Footer, Glossary, KeyboardHints
      hooks/
        useRaceData.js            races + circuit path + lap data, per-race cache
        useTelemetry.js           per-lap telemetry prefetch
        useCounterfactual.js      POST /counterfactual/simulate
        useGloryPath.js           POST /glory-path/solve
        useCommentary.js          GET /ai/commentary/{id}
        useAIChat.js              stateful conversation against /ai/ask
        useChampionshipImpact.js  POST /championship/impact
        useRealism.js             POST /counterfactual/realism
        useShowcase.js            GET /showcase
        useStats.js               GET /stats with sample fallback
        useCountUp.js             eased number animation + formatLargeNumber
      pages/
        HomePage.jsx              landing page - hero, scale strip, three pillars,
                                  AI-in-F1 narrative beats, scenarios, IBM stack, CTA
        SeasonsPage.jsx           six rich year cards
        LibraryPage.jsx           race grid; /seasons/:year scopes it
        RewindPage.jsx            TrackCanvas + Leaderboard + WhatIfPanel|AIChatBox +
                                  AINarrator + ChampionshipImpact + RealismChip +
                                  keyboard shortcuts
        GloryPathPage.jsx         glory form + animated P-countdown + step list + citations
        ForecastPage.jsx          win% + circuit-DNA radar + risks
        StatsPage.jsx             scale showcase - animated big numbers + season bars
        ShowcasePage.jsx          curated demo cards
        AboutPage.jsx             stack overview + glossary tooltips
      components/                 each in its own directory
        TrackCanvas/              telemetry-driven car renderer (do NOT touch animation)
        Leaderboard/, PlaybackControls/, CircuitDNA/, ForecastDashboard/, WhatIfPanel/
        AINarrator/, AIChatBox/, Citations/
        ChampionshipImpact/, RealismChip/, Skeleton/, Footer/
        Glossary/GlossaryTerm.jsx
        KeyboardHints/, StatHero/

  langflow/                       Exportable flow JSONs (visual graphs of pipelines)
    counterfactual_flow.json
    glory_path_flow.json
    forecast_flow.json

  docs/
    APEX_Technical_Document_v2.md
    SETUP_AND_INGEST.md
    SUPABASE_RUNBOOK.md
    ROADMAP_FOR_CLAUDE.md
    AGENT_BRIEFING.md             (this file)
```

---

## 3. Data model

PostgreSQL with **pgvector** extension. 11 tables:

```
circuits        id, name, location, country, length_km, gps_path JSONB, gps_image TEXT
drivers         id, driver_ref unique, code, forename, surname, nationality
constructors    id, constructor_ref unique, name, nationality
seasons         year PK
races           id, season_year FK, round, circuit_id FK, name, date, total_laps
race_results    id, race_id, driver_id, constructor_id, grid_position, final_position, points, status
lap_times       id, race_id, driver_id, lap, position, time_ms, gap_to_leader_ms
pit_stops       id, race_id, driver_id, stop_number, lap, duration_ms, tire_in, tire_out
safety_cars     id, race_id, type, lap_start, lap_end
telemetry_paths id, race_id, driver_id, lap, path JSONB [{x,y,t_ms,speed}]
race_embeddings id, race_id, content TEXT, embedding Vector(1536), metadata JSONB
scenarios       id, label, race_id, changes JSONB, created_at
```

Unique constraints:
- `lap_times(race_id, driver_id, lap)`
- `telemetry_paths(race_id, driver_id, lap)`
- `pit_stops(race_id, driver_id, stop_number)`
- `races(season_year, round)`

`race_embeddings.metadata` carries the **source** tag (`race_narrative`,
`fia_decision`, etc.) and `title`. This drives the citation chips in the UI.

---

## 4. API surface

| Method | Path | Returns |
|--------|------|---------|
| GET | `/` | `{ status: "ok" }` |
| GET | `/health` | counts + Granite status + pgvector status + season presence |
| GET | `/stats` | headline numbers + per-season progress + embedding sources |
| GET | `/races` | every race; ordered by season DESC, round ASC |
| GET | `/races/{id}/laps` | lap-by-lap drivers with position, gap, tire, in_pit |
| GET | `/races/{id}/telemetry/{lap}` | per-driver x/y/t_ms/speed paths |
| GET | `/circuits` | id, name, country, has_path |
| GET | `/circuits/{id}/path` | normalized GPS path |
| POST | `/counterfactual/simulate` | alt_laps, summary, explanation, citations, top5s, race_director, effective_changes |
| POST | `/counterfactual/realism` | { score, label, reasoning, source } |
| POST | `/glory-path/solve` | starting_position, achieved_position, applied, rationales, explanation, citations |
| POST | `/championship/impact` | season standings actual vs alternate + title change + narrative |
| GET | `/ai/commentary/{id}?up_to_lap=N` | Granite narrative + citations |
| POST | `/ai/ask` | Granite answer + citations |
| GET | `/forecast/{id}` | predictions, circuit_dna, risk_factors |
| GET | `/showcase`, GET `/showcase/{id}` | curated demo scenarios |
| POST | `/scenarios`, GET `/scenarios` | save/list user scenarios |

---

## 4b. AI Race Director (Option B - shipped)

When `POST /counterfactual/simulate` is called with `ai_director: true`,
the engine runs through an extra AI layer **before** the deterministic
re-rank.

**Pipeline:** `user changes -> driver_profiles -> race_director -> change_expander -> engine`

- **Triggers** that invoke the Director: `weather`, `safety_car`,
  `mechanical`, `dnf`. Other change types pass through.
- **Driver profiles** (5 axes per driver) feed into the Granite prompt so it
  can reason about who would do what.
- **Granite output** is structured JSON. The `race_director` module
  schema-validates it: unknown drivers/actions/oversized confidence are
  dropped, malformed JSON falls back to an empty plan, and the engine runs
  on the user's original changes only.
- **Action vocabulary** Granite can pick from: `pit / stay_out / retire /
  push / manage`. `change_expander` maps these to engine change types.

Response payload gains:
```
race_director: { plans: [{trigger_summary, narrative, decisions[...]}], expanded_changes: [...] }
effective_changes: [...]   # original + Director-added
```

The UI renders this as a **Race Director Notes** card below the Granite
explanation, colour-coding decisions by action tone.

## 5. The 7 counterfactual change types

Located in `backend/ai/counterfactual.py:_apply_changes`. **Driver-required**
flag marks which changes need `driver_code` in the payload.

| `change_type` | Driver? | `lap` | `value` | Effect |
|---------------|---------|-------|---------|--------|
| `pit_lap` | yes | original pit | new pit lap | Refund old pit penalty, apply on new lap |
| `dnf` | yes | retirement lap | unused | Drop all laps from `lap` onwards |
| `fastest_lap` | yes | target | new `time_ms` | Rewrite one lap's time |
| `mechanical` | yes | start lap | ms/lap penalty (default 800) | Add recurring penalty |
| `weather` | no | start lap | `{benefits:["VER","HAM"], penalty_ms:1200}` | Global penalty except listed drivers |
| `safety_car` | no | unused | start lap | Refund ~12s to anyone pitting in lap window |
| `grid_swap` | yes | switch lap | partner driver code | Swap a constant delta until lap N |

If you add a new change type:
1. Add the constant to `backend/ai/changes.py`.
2. Add the branch to `_apply_changes` in `backend/ai/counterfactual.py`.
3. Add the display string to `describe_change` in `changes.py`.
4. Add the cost to `CHANGE_BASE_COST` in `backend/ai/realism.py`.
5. Add a case to `formatValue`/`formatChange` in the relevant frontend pages.
6. Add a row to the table in this doc.

---

## 6. Branch + commit conventions

- **Branch:** all work goes on `claude/analyze-project-jBgIH`. Never push to `main`.
- **Commit message:** start with an area prefix and imperative verb. Examples:
  - `feat: championship impact card`
  - `refactor: dedupe describe_change helpers`
  - `docs: add Supabase runbook`
  - `fix: AIChatBox stale-state on suggestion click`
- **Never** include the model name or "Claude" in commit messages, code
  comments, or PR bodies. The trailing footer that's already in commits is
  fine to keep.
- **Push:** `git push -u origin claude/analyze-project-jBgIH`. Don't open PRs
  unless explicitly asked.
- **Never** `--no-verify`, `--force` to main, `git reset --hard` to discard
  the user's changes, or `git checkout .` to clobber working tree.

---

## 7. Code conventions (follow these or revert)

### Python
- Type hints on every public function. `from __future__ import annotations`
  at the top so `dict[str, int]` works on 3.10+.
- No `except: pass` - either re-raise or return a structured fallback like
  the rest of the codebase.
- No `print()` in API handlers - it shows up in uvicorn logs and confuses
  users. Use it in CLI scripts only (and flush=True for tqdm interop).
- Module-private helpers start with `_`. Use them; don't export.
- Granite/IBM calls **must** have a fallback path so the demo never breaks
  without credentials. Look at `ai/realism.py` for the pattern.

### JSX
- ESM imports only - `import { X } from "./Y.js"` (note the `.js`/`.jsx`).
- No emojis in user-facing strings or component output.
- Use the arrow character `->` not `→` for compatibility.
- Hooks always go in `frontend/src/hooks/use<Name>.js`, return `{ data, isLoading, error, load, reset }` where applicable.
- Reuse existing CSS classes before adding new ones; the design tokens live
  in `styles/base.css` (`--f1-red`, `--bg-1`, `--text-mid`, etc.).
- The big stylesheets are already split (`base/layout/components/pages/home/stats/extras`). Add new rules to the right file - don't create a new top-level CSS file unless the concept doesn't fit any of them.

### Tests
- Pure-logic tests live in `backend/tests/`. They must not need Postgres or
  IBM keys. Mock with `monkeypatch.delenv` for the IBM fallback path.
- Run them after any backend change: `pytest tests/ -v`. Must pass 18+.

---

## 8. Where to put new files

| You're adding... | Put it in |
|------------------|-----------|
| A new FastAPI router | `backend/api/<name>.py`, register in `backend/main.py` |
| Granite/RAG logic | `backend/ai/<name>.py` |
| A new change type helper | extend `backend/ai/changes.py` - never duplicate |
| A new Race Director action verb | add to `VALID_ACTIONS` in `race_director.py` AND to the mapper in `change_expander.py:expand_decision`. Both files or neither. |
| An ingestion script | `backend/ingestion/<name>.py`; private helpers `_name.py` |
| A SQLAlchemy column or table | `backend/db/models.py` + new Alembic revision |
| A pytest | `backend/tests/test_<name>.py` (no DB unless you mock the session) |
| A frontend page | `frontend/src/pages/<Name>Page.jsx` + route in `App.jsx` |
| A reusable widget | `frontend/src/components/<Name>/<Name>.jsx` |
| A hook | `frontend/src/hooks/use<Name>.js` |
| Static data / fallback | `frontend/src/data/<name>.js` - no React in this dir |
| New CSS | the appropriate file in `frontend/src/styles/` |

---

## 9. Verification checklist (before declaring "done")

```bash
# Backend
cd backend
python -c "import ast, os
for root, _, files in os.walk('.'):
    if any(x in root for x in ['.venv', '__pycache__', 'migrations']): continue
    for f in files:
        if f.endswith('.py'):
            ast.parse(open(os.path.join(root, f)).read())
print('OK')"

pytest tests/ -v       # must show 48+ passed

# Frontend
cd frontend
npm run build          # must finish without errors
```

If you broke either of those, you didn't finish the task. Fix it before
committing.

---

## 10. Things that will get you yelled at

1. **Re-introducing `_describe_change` in any file other than `backend/ai/changes.py`.**
2. **Creating a new top-level `styles.css`** - it was split for a reason.
3. **Moving files in `data/`, `styles/`, `tests/`, or `ai/` without updating every importer.**
4. **Adding a Python dependency without putting it in `requirements.txt`.**
5. **Adding a new change type without updating `describe_change`, `CHANGE_BASE_COST`, the WhatIfPanel dropdown, AND this doc's table.**
6. **Calling Granite from inside a hot loop.** Each call is 1-3 seconds. Loop the deterministic engine, call Granite once at the end.
7. **Breaking the no-IBM-credentials path.** Every Granite call site must
   degrade gracefully (look at `ai/realism.py:score_counterfactual` -
   try/except around `generate()`, fall back to the heuristic).
8. **Hardcoding race IDs in the frontend.** Use `useRaceData()` or
   `useStats()` to discover them at runtime.
9. **Using `setTimeout(fn, 0)` to work around stale state.** Lift state up,
   or pass the value as an argument. See `AIChatBox` for the right pattern.
10. **Breaking sample-data fallbacks.** `LibraryPage`, `StatsPage`, and the
    Home scale strip must render reasonable content when the backend is
    down. Test by stopping uvicorn and reloading.

---

## 11. The "what should I work on?" decision tree

```
START
  |
  v
Does the user have a specific task? -- yes --> Do it. Verify with section 9.
  | no
  v
Is the user demoing? -- yes --> Check that:
  |                              - the backend is up (curl /health)
  |                              - /stats returns non-zero numbers
  |                              - one Showcase scenario works end-to-end
  |                              Don't ship more features mid-demo.
  | no
  v
Open docs/ROADMAP_FOR_CLAUDE.md.
Pick the lowest-numbered, smallest task whose acceptance test you can verify.
Don't go bigger. Land it. Push. Move on.
```

---

## 12. Single-paragraph elevator pitch (for prompts)

> APEX Race Director is an IBM-stack F1 alternate-history simulator. The
> backend (FastAPI + Postgres + pgvector + watsonx.ai Granite) indexes
> every race 2019-2024 - laps, pit stops, telemetry, safety cars, FIA
> stewards' decisions - and the React/Vite frontend lets a user replay
> any Grand Prix with Granite commentary, run "what-if" scenarios across
> 7 change types, see the championship flip in real time via the
> Championship Impact card, and solve "Glory Paths" that find the smallest
> set of changes to lift a driver to a target finish position. Built on
> branch `claude/analyze-project-jBgIH`. 18 pytest smoke tests, full Vite
> build, every Granite call has a heuristic fallback so demos never break.

Use that paragraph to seed your own system prompt when continuing work.

---

**You're now caught up.** Open `docs/ROADMAP_FOR_CLAUDE.md` for the task list.
