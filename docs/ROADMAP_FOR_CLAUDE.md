# APEX Roadmap - for cheaper Claude models to follow

**Audience:** Claude Sonnet / Haiku continuing the build after the Opus passes.
**Goal:** Each task below is intentionally narrow, with files, expected diffs, and an acceptance check that's easy to verify.

Work top-to-bottom. Each task lists the **files** touched, what to **do**, and an **acceptance** check (a grep, a curl, or a UI behaviour). Don't skip the acceptance step.

## What's already done (don't redo)

- [x] Championship Impact endpoint + card (`backend/ai/championship.py`, `frontend/.../ChampionshipImpact/`)
- [x] Realism Score endpoint + chip (`backend/ai/realism.py`, `frontend/.../RealismChip/`)
- [x] Showcase page + curated scenarios (`backend/ai/showcase_scenarios.py`, `frontend/.../ShowcasePage.jsx`)
- [x] Health/diagnostics endpoint (`backend/api/health.py`) + Footer chip surface
- [x] Skeleton loaders (`Skeleton/Skeleton.jsx`) wired into LibraryPage
- [x] Glory Path animated `P-start -> P-achieved` countdown
- [x] Keyboard shortcuts on Time Machine (Space / ←→ / R)
- [x] Glossary tooltips (`Glossary/GlossaryTerm.jsx`) used on AboutPage
- [x] Test suite: 18 passing pytest smoke tests under `backend/tests/`
- [x] Folder restructure: `backend/utils/` removed, `frontend/src/data/`, `frontend/src/styles/` split
- [x] Stats page (`/stats`) + `/stats` endpoint + StatHero/StatStrip animated count-ups
- [x] Scale strip on Library + About showing live Grand Prix / Laps / Pit stops / Data points
- [x] Better bulk ingestion: tqdm progress, per-year totals, `--parallel-years`, `--full-telemetry`
- [x] `ingestion.status` CLI - per-season progress bars
- [x] `ingestion.export` CLI - DB to JSON dump for portability
- [x] Expanded `sampleData.js` from 1 race to 28 sample races across 2019-2024

The remaining waves stay below.

Prerequisites you can take for granted:
- The branch `claude/analyze-project-jBgIH` already contains the architecture in `docs/APEX_Technical_Document_v2.md`.
- `backend/main.py` registers all seven routers; do not duplicate.
- The frontend builds with `npm run dev` from `frontend/`. The backend boots with `uvicorn main:app --reload` from `backend/`.

When in doubt: read `docs/APEX_Technical_Document_v2.md` first.

### Where to put new files

| You're adding... | Put it in |
|------------------|-----------|
| A new FastAPI router | `backend/api/<name>.py`, register in `backend/main.py` |
| AI logic (prompt, retrieval, search) | `backend/ai/<name>.py` |
| A shared change-type helper | extend `backend/ai/changes.py`, don't duplicate |
| An ingestion script | `backend/ingestion/<name>.py` (private helpers prefixed `_`) |
| A SQLAlchemy model field | `backend/db/models.py` + new Alembic migration |
| A page | `frontend/src/pages/<Name>Page.jsx`, route in `App.jsx` |
| A reusable widget | `frontend/src/components/<Name>/<Name>.jsx` |
| A hook | `frontend/src/hooks/use<Name>.js` |
| Static data / fallbacks (no logic) | `frontend/src/data/<name>.js` |
| New CSS | the appropriate file in `frontend/src/styles/` (base / layout / components / pages). Don't create `styles.css` again. |

---

## Wave 1 - Data & ingestion (low risk, high value)

### Task 1.1 - Run the bulk ingestion

**Do:**
```bash
cd backend
python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024 --skip-telemetry --skip-embeddings
```

Then a second pass:
```bash
python -m ingestion.run_bulk --years 2024 --skip-telemetry
python -m ingestion.embed_races --years 2019 2020 2021 2022 2023 2024
```

**Acceptance:**
- `psql -c "select season_year, count(*) from races group by 1 order by 1"` shows 18-24 rows per year.
- `psql -c "select count(*) from race_embeddings"` is > 800.

If a year fails partway: re-run, it's restart-safe.

### Task 1.2 - Add seed FIA decisions

There are no FIA PDFs in the repo yet (deliberately - they're large). Add a `backend/fia_pdfs/` directory and document the convention:

**Files to add:**
- `backend/fia_pdfs/.gitkeep`
- `docs/FIA_INGESTION.md` (10-line readme: where to drop PDFs, how to map to race_id)

Update `.gitignore` so `backend/fia_pdfs/*.pdf` are ignored. Run:
```bash
python -m ingestion.fia_parser backend/fia_pdfs/
```

**Acceptance:** `select source, count(*) from race_embeddings group by 1;` shows a `fia_decision` row when any PDF exists.

### Task 1.3 - Seed sample fallback for Glory Path

Currently `LibraryPage` falls back to `sampleData.sampleRaces` (one race only) when the backend is unreachable. Extend `frontend/src/data/sampleData.js` so a no-backend demo can still show Library cards for at least four races across two seasons. Don't touch anything else.

**Acceptance:** stop the backend, reload `/`, you still see ≥4 race cards.

---

## Wave 2 - Visual polish

These tasks are pure CSS / small JSX tweaks. No new endpoints.

### Task 2.1 - Hover preview for citation chips

**Files:** `frontend/src/components/Citations/Citations.jsx`, `frontend/src/styles/components.css`

Right now hovering a `.citation` chip shows the full snippet through the `title=` attribute. Replace that with a styled popover (CSS-only, using `position: absolute` and `:hover`). Show: title, score, snippet first 240 chars.

**Acceptance:** hovering a chip on Glory Path shows a styled card, not a tooltip.

### Task 2.2 - Pulse the leader pill

**Files:** `frontend/src/styles/components.css` (extend `.hud-pill.live`)

Add a second pulse keyframe that scales the green dot from 1 -> 1.6 -> 1 every 1.6s.

**Acceptance:** the green LIVE pill on the track HUD pulses.

### Task 2.3 - Skeleton loaders on the Leaderboard

`SkeletonRow` / `SkeletonCard` already exist (`frontend/src/components/Skeleton/Skeleton.jsx`) and are wired into LibraryPage. Extend them to the Leaderboard so a lap with no drivers renders 6 `SkeletonRow`s instead of nothing.

**Files:** `frontend/src/components/Leaderboard/Leaderboard.jsx`

**Acceptance:** load a race before lap data arrives; see shimmer rows.

### Task 2.4 - Glory Path arrow animation polish

The number countdown is done (`AnimatedPosition` in `GloryPathPage.jsx`). Add a horizontal slide-in for the green `->` arrow so the visual transition feels complete.

**Files:** `frontend/src/pages/GloryPathPage.jsx`, `frontend/src/styles/pages.css` (or extras.css)

**Acceptance:** when a result arrives the arrow slides from left, opacity 0->1.

### Task 2.5 - Tire compound icons on PitStop

The `LapTime.tire` value is a single letter (S/M/H/I/W). Already styled. Add a small SVG donut next to the letter in `.tire-badge` (use inline SVG with `currentColor`).

**Acceptance:** leaderboard rows show a colored donut + letter.

---

## Wave 3 - Backend extensions

### Task 3.1 - Extend `safety_car` change to influence position

Currently `safety_car` only refunds pit penalty time. Improve it: compress all gap_to_leader values within the SC window to a maximum of 1500 ms (simulates the field bunching). Edit `backend/ai/counterfactual.py:_apply_changes`.

**Acceptance:** simulate `safety_car` at lap 10 with a baseline race; gaps at lap 11 should be ≤1.5s.

### Task 3.2 - Wet / damp tire compounds

Add `tire_in/tire_out` parsing in `backend/ingestion/ergast.py:ingest_pit_stops`. Ergast doesn't carry tire labels; pull them from FastF1 via `ingestion/fastf1_loader.py` instead. Add a new function `load_tires_for_race(year, round)` that updates the `pit_stops.tire_in`/`tire_out` columns.

**Acceptance:** `select tire_out, count(*) from pit_stops group by 1` shows S/M/H values.

### Task 3.3 - "Compare two simulations" endpoint

`POST /counterfactual/compare` accepts `{ race_id, scenario_a: changes[], scenario_b: changes[] }` and returns both `alt_laps` plus a position-by-position diff per driver on the final lap.

**Files:** new `backend/api/counterfactual.py` route, no new ai module needed (call `simulate_counterfactual` twice).

**Acceptance:** `curl -X POST localhost:8000/counterfactual/compare -d '...'` returns `{ a: {...}, b: {...}, diff: [{code, a_pos, b_pos, delta}] }`.

### Task 3.4 - Persist Glory Path results

When a Glory Path is solved, save it as a `Scenario` with a generated label like "Glory: HAM -> P1 (Monaco 2023)". Edit `backend/ai/glory_path.py`.

**Acceptance:** `GET /scenarios` includes the entry after a solve.

### Task 3.5 - Champion timeline endpoint

Add `GET /drivers/{code}/season-points/{year}` that returns `[{round, race_name, points, cumulative_points}]`.

**Files:** new `backend/api/drivers.py`, register in `backend/main.py`.

**Acceptance:** `curl localhost:8000/drivers/VER/season-points/2023` returns a 22-row array.

---

## Wave 4 - New frontend pages

### Task 4.1 - Driver page

**Route:** `/driver/:code/:year`
**Files:** new `frontend/src/pages/DriverPage.jsx`, route in `App.jsx`.

Show: driver header (name + team color + nationality), Recharts line chart of cumulative points across the season (from Task 3.5), table of races + finishing positions. Add a navigation link from any leaderboard row's driver code (clicking the driver pill in Leaderboard.jsx navigates to `/driver/{code}/{year}`).

**Acceptance:** click `VER` on Monaco 2023 leaderboard -> see VER season chart.

### Task 4.2 - Compare scenarios page

**Route:** `/compare/:raceId`
**Files:** new `frontend/src/pages/ComparePage.jsx`, hook `useScenarioCompare.js`, uses the endpoint from Task 3.3.

Left rail: two WhatIfPanel instances (A and B). Center: side-by-side final classification tables with up/down arrows showing the delta.

**Acceptance:** apply different changes in A vs B, click Compare, see position deltas.

### Task 4.3 - Standings page

**Route:** `/standings/:year`
**Files:** new `frontend/src/pages/StandingsPage.jsx`. Aggregates `RaceResult.points` from the existing `/races` data without needing a new endpoint.

**Acceptance:** opens with a sortable table of 2024 driver totals.

---

## Wave 5 - Smarter AI

### Task 5.1 - Streaming Granite responses

`backend/ai/granite.py` currently makes a single POST. watsonx supports SSE streaming through `/ml/v1/text/generation_stream`. Add `generate_stream(prompt, ...)` that yields chunks. Update `POST /ai/ask` to use FastAPI's `StreamingResponse`.

In the frontend, `useAIChat` becomes a generator hook that updates the last message as chunks arrive.

**Acceptance:** the chat box shows text typing in token-by-token.

### Task 5.2 - Replace heuristic forecast with Granite-judge

Currently `ai/forecast.py:_recent_form` is a closed-form heuristic. Add an alternative path that:
1. Builds the same per-driver feature vector (avg_pos, recent_points, has_pole_history at this circuit).
2. Asks Granite to *rank* the drivers and provide a one-line strategy each.
3. Keeps the heuristic as a fallback when no IBM key is configured.

**Acceptance:** with credentials, the strategy text varies between races (current heuristic produces only 4 distinct strings).

### Task 5.3 - "Coach me" mode in Glory Path

After solving, post-process the candidate list to keep the rationale strings concise. Have Granite expand each rationale into a single coach-style sentence ("the lap-32 pit was 2.1s slower than your average - move it three laps earlier to keep tire delta").

**Acceptance:** `GloryPathPage` rationale lines read like coaching, not data.

### Task 5.4 - Granite-judged "realism score"

For a counterfactual, score how realistic it is (0-1). Granite gets the changes + race context and emits a number + reasoning. Surface as a chip in the `sim-note`.

**Acceptance:** unrealistic combos (e.g. winning driver retires + weather penalty on second-place) score < 0.3.

---

## Wave 6 - Demo polish

### Task 6.1 - Add a "Showcase" pre-baked scenario

A `/showcase` route that auto-runs through three pre-recorded simulations on a 6-second timer per scene. Useful for a hands-free demo.

### Task 6.2 - Sound effects (optional)

Add a low-volume engine drone when the track canvas is playing. `frontend/src/assets/engine.mp3`, play via Web Audio with mute toggle in PlaybackControls.

### Task 6.3 - README hero update

The current `README.md` is a Windows setup snippet. Rewrite as a hackathon README: hero paragraph, screenshots, IBM-stack callouts, demo URLs. Keep the setup section at the bottom.

---

## Code conventions for follow-on agents

1. **No new top-level dependencies** unless a task explicitly asks. The existing `requirements.txt` covers the build.
2. **No "TODO" or "FIXME" comments.** Implement or skip the task; don't leave breadcrumbs.
3. **Never silently catch exceptions in `except: pass`.** Either re-raise or return a structured fallback like the rest of the codebase.
4. **Frontend strings** stay ASCII. The arrow character used in this codebase is `->` not the Unicode arrow.
5. **Commit messages** follow `<area>: <imperative>` e.g. `frontend: streaming AI chat hook`. Don't reference the model ID.
6. **Branch:** all work continues on `claude/analyze-project-jBgIH`. Push with `git push -u origin claude/analyze-project-jBgIH`.

---

## What's deliberately NOT in this roadmap

- Auth / user accounts (out of scope for hackathon).
- Multi-tenancy / scenario sharing (the `Scenario` table is enough for single-user persistence).
- Live race ingestion (we're a historical simulator).
- Mobile-native UI (the responsive CSS is good enough on tablets).
- Test suite (the engine is small and the demo is the test).

If a request lands that touches any of the above, escalate: don't silently add it.

---

## Quick-reference grep cheatsheet

```bash
# all router registrations
grep -rn "app.include_router" backend/

# every Granite call site
grep -rn "from ai.granite import" backend/

# all RAG retrieve calls
grep -rn "build_race_context" backend/

# frontend routes
grep -n "Route path" frontend/src/App.jsx

# every change_type the engine understands
grep -n "change_type ==" backend/ai/counterfactual.py
```
