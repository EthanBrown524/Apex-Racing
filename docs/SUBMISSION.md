# APEX Race Director - IBM May 2026 Challenge submission

This file collects everything you need to paste into the BeMyApp submission
form, plus the 3-minute video script.

---

## Project name

**APEX Race Director**

## Short description (140 chars)

> AI-powered F1 alternate-history simulator. Replay any 2019-2024 Grand Prix, rewrite strategy, watch the championship flip — explained by IBM Granite.

## Long description / problem statement

> Formula 1 is the most data-intensive sport in the world, but the questions
> fans care most about are counterfactual — "what if Verstappen's engine had
> broken at Abu Dhabi 2021?" "what if Leclerc had pitted earlier at Monaco
> 2022?" No tool answers them with rigor.
>
> APEX turns every Grand Prix from 2019-2024 into an editable timeline. The
> What-If Lab applies one of seven physical change types (pit, DNF, weather,
> safety car, mechanical, grid swap, fastest lap). A deterministic Python
> simulator recomputes lap-by-lap positions. The Championship Impact card
> recomputes the whole season's standings under the counterfactual. IBM
> Granite narrates every outcome with citations into a 5,260-chunk RAG index
> across race narratives, FIA stewards' decisions, and FIA technical
> regulations. The AI Race Director uses Granite as a planner — given a
> trigger event, it emits a strict-JSON plan of how every other driver would
> respond, which is then expanded into engine changes and re-simulated.

## IBM stack usage (paste verbatim)

> - **IBM Granite-3-8b-instruct (watsonx.ai):** counterfactual explanations,
>   free-form Q&A (streaming over SSE), Glory Path storylines + coach-me
>   rewrites, Race Director planning (structured JSON), Realism scoring,
>   Forecast re-ranking + strategy text. Every Granite call is
>   graceful-degrading so the demo never breaks.
> - **IBM Slate-30m-english-rtrvr (watsonx.ai embeddings):** 5,260 RAG chunks
>   across race narratives, FIA stewards' decisions, and FIA technical
>   regulations.
> - **Docling:** extracts FIA decision PDFs into structured markdown for the
>   RAG index. See `docs/FIA_INGESTION.md`.
> - **Langflow:** three exportable visual flow graphs (counterfactual,
>   glory-path, forecast) in `langflow/*.json`.

## Why this matters in the context of racing

Pulled from README "Why this matters" section - paste that block in.

## Tech stack

React 19 + Vite · FastAPI · PostgreSQL + pgvector (Supabase) · SQLAlchemy 2 ·
Alembic · IBM watsonx.ai (Granite + Slate) · Docling · Langflow · FastF1 ·
Ergast (jolpi.ca mirror) · pypdfium2

## GitHub repo

https://github.com/EthanBrown524/Apex-Racing

## CI

GitHub Actions runs the 94-test pytest suite on every push and PR.
See [`.github/workflows/test.yml`](../.github/workflows/test.yml).

## Verified live numbers

```
races              128     (2019: 21, 2020: 17, 2021-23: 22 each, 2024: 24)
drivers             37
race_results      2,559
lap_times       140,202
pit_stops         3,487     (3,220 with tire compound: 92% coverage)
safety_cars         148     (84 SC + 64 VSC)
telemetry_paths  22,977
race_embeddings   5,260     (race_narrative: 383 · fia_regulation: 4,840 · fia_decision: 37)
```

---

## 3-minute video script

| Time | Beat | Talking point |
|---|---|---|
| 0:00 | Home hero | "APEX Race Director — every Grand Prix from 2019-2024, an editable timeline. Built on IBM Granite + Slate." Pan the live numbers strip. |
| 0:20 | `/showcase` page | Click **Abu Dhabi 2021** card. "The most controversial F1 race in a decade — let's see what would have happened if Verstappen's engine had broken." |
| 0:30 | Time Machine, playback | Show telemetry-driven cars on the circuit canvas, leaderboard updating. Pause around lap 50. |
| 0:50 | Open What-If Lab | "I've pre-loaded a mechanical issue for Verstappen on lap 53. Let's simulate." |
| 1:00 | Granite explanation streaming | "Granite is reading the race context and 6 RAG citations and writing the explanation token-by-token." Watch text appear. |
| 1:15 | Realism Score chip | "0.26 — Fantasy. Granite judges that scenario as implausible, and explains why." |
| 1:25 | Championship Impact | Click **Show championship impact**. "If this had happened, **Hamilton wins the 2021 World Championship.** Verstappen drops 18 pts, Sainz picks up 3." This is the moneyshot. |
| 1:45 | Toggle AI Race Director | "Let's give Granite the same trigger, but this time as a planner." Run again. Show Race Director Notes card with per-driver decisions: who pits, who gambles, who retires. |
| 2:00 | Glory Path: Alonso Spain 2023 | "Glory Path asks: what's the minimum set of changes to get Alonso to P1?" Click solve. Animated P7 → P3. Show coach-me rationale lines. |
| 2:30 | Compare A vs B | Two scenarios side-by-side on Monaco 2022. Show the delta table — Leclerc swings 5 positions. |
| 2:45 | Forecast / FIA citations | Open Forecast for a 2024 race. Hover a citation chip — popover shows the actual FIA decision text Docling extracted. |
| 2:55 | Cut to Footer chips | Granite configured ✓ · pgvector on ✓ · 128 races · 5260 RAG chunks. "Everything live, everything cited. Thanks." |

Total: 3:00. If you go over, drop the Forecast beat and the AI Race Director toggle.

## Submission checklist

- [x] Public GitHub repo
- [x] Functioning prototype (live Supabase + IBM watsonx)
- [x] README with problem / approach / why-it-matters
- [x] Uses ≥1 IBM technology (uses **3**: Granite, Slate, Docling, plus Langflow)
- [x] LICENSE (MIT)
- [x] Continuous integration (GitHub Actions)
- [x] 94 automated tests
- [ ] Video (≤3 min) — use script above
- [ ] BeMyApp submission form — paste the blocks from this doc
- [ ] After judging closes: rotate Supabase + IBM credentials

## Pre-submission smoke test (run locally)

```bash
# 1. Backend
cd backend && uvicorn main:app --port 8000

# 2. Endpoint sweep (separate terminal)
curl localhost:8000/health
curl -X POST localhost:8000/counterfactual/simulate -H "Content-Type: application/json" \
  -d '{"race_id":66,"changes":[{"driver_code":"VER","change_type":"mechanical","lap":53,"value":1500}]}'
curl -X POST localhost:8000/championship/impact -H "Content-Type: application/json" \
  -d '{"race_id":66,"changes":[{"driver_code":"VER","change_type":"mechanical","lap":53,"value":1500}]}'

# 3. Frontend
cd frontend && npm run dev    # then visit http://localhost:5173

# 4. Tests
cd backend && pytest tests/ -v
```
