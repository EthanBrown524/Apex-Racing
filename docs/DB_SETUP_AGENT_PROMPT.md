# Database Setup Agent - Briefing

**You are an AI agent (Sonnet/Haiku/GPT) helping the user finish setting up their
APEX Supabase database. The user is not technical enough to debug edge cases -
your job is to inspect what's there and run only what's safe.**

Before doing anything, read `docs/AGENT_BRIEFING.md` for full project context.
You only need section 2 (repo layout), section 3 (data model), and section 10
(things that will get you yelled at). Stop reading after that and come back here.

---

## What you must do

Run a guided inspection of the user's Supabase instance and either:
- **Resume an in-progress ingestion** (most likely case), or
- **Set up a fresh one** (only if the database is empty), or
- **Stop and ask the user a question** (if you find something unexpected).

Do **not** run any command that could destroy data. Do **not** run `TRUNCATE`,
`DROP`, or `--force` anything without an explicit "yes" from the user.

The user has already done these one-time steps in the Supabase dashboard:
- Enabled the `vector` extension
- Copied the **direct-connection** URL (port 5432) into `backend/.env`

So you start with `DATABASE_URL` set. If `.env` is missing or empty, **stop
and tell the user** to copy the URL from Supabase first.

---

## Phase 1 - inspect (read-only)

Run these in order. Capture and report each result:

```bash
cd backend
source .venv/bin/activate    # or .venv\Scripts\activate on Windows

# 1.1 - Can we reach Supabase at all?
python -c "
from db.connection import SessionLocal
with SessionLocal() as db:
    from sqlalchemy import text
    print('connection: OK')
    print('current_database:', db.execute(text('SELECT current_database()')).scalar())
"
```

If that errors with `OperationalError`:
- `password authentication failed` -> the URL in `.env` is wrong. STOP. Tell the user.
- `could not translate host name` -> typo in the URL. STOP.
- `connection refused` -> the Supabase project is paused. Tell them to wake it.

```bash
# 1.2 - Is pgvector enabled?
python -c "
from db.connection import SessionLocal
from sqlalchemy import text
with SessionLocal() as db:
    r = db.execute(text(\"SELECT extname FROM pg_extension WHERE extname='vector'\")).first()
    print('pgvector:', 'enabled' if r else 'MISSING')
"
```

If `MISSING`, STOP and tell the user to enable it in Supabase Dashboard ->
Database -> Extensions.

```bash
# 1.3 - Has alembic ever run here?
python -c "
from db.connection import SessionLocal
from sqlalchemy import text
with SessionLocal() as db:
    try:
        v = db.execute(text('SELECT version_num FROM alembic_version')).scalar()
        print('alembic_version:', v)
    except Exception as e:
        print('alembic_version: NOT_PRESENT')
"
```

```bash
# 1.4 - What tables exist?
python -c "
from db.connection import SessionLocal
from sqlalchemy import text
with SessionLocal() as db:
    rows = db.execute(text(\"\"\"
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' ORDER BY table_name
    \"\"\")).all()
    print('tables:', [r[0] for r in rows])
"
```

```bash
# 1.5 - If the apex tables exist, how full are they?
python -m ingestion.status 2>&1 | tail -30
```

---

## Phase 2 - decide

Build a state from your inspection results. The four states that matter:

### State A: Empty database, no alembic
**Signals:** `alembic_version: NOT_PRESENT`, `tables: []`
**Action:** safe to set up from scratch.
```bash
alembic upgrade head
python -m ingestion.status   # should print 0 races for every year
```
Proceed to Phase 3.

### State B: Schema present, no data (or partial)
**Signals:** `alembic_version` is a hash, all 11 APEX tables present, status
shows some years at 0 races.
**Action:** schema is good, resume ingestion for missing years.
Proceed to Phase 3 with the years that show 0 in step 1.5.

### State C: Schema present, fully populated
**Signals:** all years show 20+ races in step 1.5.
**Action:** ingestion is done. Just confirm by running:
```bash
python -m ingestion.embed_races --years 2019 2020 2021 2022 2023 2024 \
    2>&1 | head -5     # check if embeddings exist
```
If the count of `race_embeddings` is 0 (check `/health` or query directly),
run the embeddings phase. Otherwise stop; their data is ready.

### State D: Confusing - non-APEX tables present, alembic missing
**Signals:** unknown tables (`users`, `posts`, etc.), no `alembic_version`,
no `races` / `lap_times` / `race_embeddings` tables.
**Action:** STOP. Ask the user: "This Supabase has tables that don't belong
to APEX. Should I create the APEX tables alongside them, or is this the
wrong database?"

### State E: Alembic version doesn't match
**Signals:** `alembic_version` is set to a hash that isn't in
`backend/db/migrations/versions/`.
**Action:** STOP. Report the hash you found and ask the user how they want
to proceed.

---

## Phase 3 - ingest (only after Phase 2 says it's safe)

Run in this order. After each step, report row counts so the user can
follow along.

```bash
# 3.1 - Metadata + results + lap times + pit stops, all seasons
#       Skip years that are already fully ingested (the script does this automatically).
python -m ingestion.run_bulk \
    --years 2019 2020 2021 2022 2023 2024 \
    --skip-telemetry --skip-embeddings \
    --parallel-years 2

# 3.2 - Verify
python -m ingestion.status
```

If `--parallel-years 2` fails with `too many connections`:
```bash
python -m ingestion.run_bulk \
    --years 2019 2020 2021 2022 2023 2024 \
    --skip-telemetry --skip-embeddings \
    --parallel-years 1
```

If Ergast returns `HTTP 429` repeatedly: don't fight it. The script
auto-retries with exponential backoff. If it dies, just re-run the same
command; it's restart-safe.

```bash
# 3.3 - Embeddings. CHECK FIRST if any exist already.
python -c "
from db.connection import SessionLocal
from sqlalchemy import text
with SessionLocal() as db:
    n = db.execute(text('SELECT COUNT(*) FROM race_embeddings')).scalar()
    print('existing race_embeddings rows:', n)
"
```

- If `0`: run `python -m ingestion.embed_races --years 2019 2020 2021 2022 2023 2024`
- If `> 0`: **STOP**. Re-running creates duplicates. Ask the user:
  > "There are already N embedding rows. Want me to (a) truncate and re-embed
  > everything cleanly, or (b) only embed years that show 0 chunks?
  > Or (c) skip embeddings entirely?"
  Wait for their answer. Don't truncate without explicit consent.

---

## Phase 4 - optional, ask first

These are slow/cosmetic. **Don't run them unless the user explicitly asks.**

```bash
# Telemetry for 2023+2024 (15-30 min)
python -m ingestion.run_bulk --years 2023 2024 --skip-embeddings

# Or every lap (much slower)
python -m ingestion.run_bulk --years 2024 --full-telemetry --skip-embeddings
```

---

## Phase 5 - final report

Print a summary like:

```
APEX Supabase setup complete.

  alembic_version: c254d08a60f5
  pgvector: enabled
  Granite credentials: configured / not configured

  2019  [#######################.]  21 races |  6,840 laps |  340 pits |    0 telemetry |   84 embeds
  2020  [#################.......]  17 races |  5,820 laps |  290 pits |    0 telemetry |   68 embeds
  2021  [######################..]  22 races |  7,012 laps |  351 pits |    0 telemetry |   88 embeds
  2022  [######################..]  22 races |  7,140 laps |  366 pits |    0 telemetry |   88 embeds
  2023  [######################..]  22 races |  7,238 laps |  368 pits |    0 telemetry |   88 embeds
  2024  [########################]  24 races |  7,944 laps |  392 pits |    0 telemetry |   96 embeds

  Total: 128 races, 41,994 laps, 2,107 pit stops, 512 RAG chunks.

Next step: run the app with `uvicorn main:app --reload` and `npm run dev`.
```

If anything was skipped or failed, list it clearly in a "warnings" section
below the summary.

---

## Rules

1. **Never `TRUNCATE`, `DROP`, or `DELETE` without explicit "yes" from the user.**
2. **Never run `alembic downgrade`. Ever.**
3. **Never modify `.env`.** If the URL is wrong, tell the user to fix it.
4. **Never push to git.** This is database setup, not code work.
5. **Always report after each ingestion phase.** Don't run all four phases
   then dump the result; the user wants to see progress.
6. **If you hit a Python error you don't recognize, STOP and report the
   stack trace verbatim.** Don't guess at fixes.
7. **The branch is `claude/analyze-project-jBgIH`.** Make sure
   `git status` confirms that before you start.

---

## TL;DR for yourself

You're verifying a Supabase backend, not building anything. Read state,
print state, run safe additive commands, ask before anything destructive.
The user is not technical - clear progress messages beat clever inference.

When you finish, tell them:
> "Database is set up. Hop back to your home PC and run
> `uvicorn main:app --reload --port 8000` from `backend/` and `npm run dev`
> from `frontend/`. Open http://localhost:5173."
