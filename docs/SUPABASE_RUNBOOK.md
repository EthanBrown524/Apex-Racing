# APEX on Supabase - Command Runbook

Everything you need to run, in order, against a Supabase Postgres. Copy-paste
top to bottom on a fresh checkout. The whole thing takes 15-30 minutes
depending on Ergast latency.

> **Branch:** all work happens on `claude/analyze-project-jBgIH`.
> Make sure you're on it: `git checkout claude/analyze-project-jBgIH`

---

## 0. One-time Supabase prep

In the **Supabase dashboard**:

1. **Database -> Extensions** -> search `vector` -> click **Enable**. This
   installs pgvector. Without it the embeddings stay as text and RAG runs in
   slow Python fallback mode.
2. **Settings -> Database -> Connection string** -> copy the **URI** under the
   "Connection string" section. Use the **direct connection** (port `5432`),
   **not** the pooler (`6543`). The pooler is pgbouncer and breaks Alembic
   migrations.

It will look like:
```
postgresql://postgres:YOUR-PASSWORD@db.abcdefgh.supabase.co:5432/postgres
```

---

## 1. Project setup (run once)

```bash
git checkout claude/analyze-project-jBgIH
git pull

# .env from the example
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.abcdefgh.supabase.co:5432/postgres
FRONTEND_URL=http://localhost:5173

# Optional - leave blank for the local hash-vector fallback
IBM_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Supabase has a connection cap; keep these small
DB_POOL_SIZE=4
DB_MAX_OVERFLOW=0
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

---

## 2. Backend - install + migrate

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# Creates all 11 tables in Supabase
alembic upgrade head
```

If `alembic upgrade head` fails with `relation "vector" does not exist`, you
forgot step 0.1 - go enable the pgvector extension in the Supabase dashboard.

---

## 3. Ingest 2019-2024 (the long part)

### 3a. Metadata + results + lap times + pit stops (5-10 min total)

```bash
python -m ingestion.run_bulk \
  --years 2019 2020 2021 2022 2023 2024 \
  --skip-telemetry --skip-embeddings \
  --parallel-years 2
```

> `--parallel-years 2` is the safe ceiling on Supabase free tier. Higher hits
> the 60-connection cap. Drop to `--parallel-years 1` if you see
> `FATAL: too many connections for role "postgres"`.

### 3b. Build the AI/RAG index (2-5 min)

```bash
python -m ingestion.embed_races \
  --years 2019 2020 2021 2022 2023 2024
```

### 3c. (Optional, slow) Telemetry for animated car positions (15-30 min)

```bash
# Sample 10 laps per race for the most recent two seasons
python -m ingestion.run_bulk --years 2023 2024 --skip-embeddings

# Or every lap (much slower, much prettier):
python -m ingestion.run_bulk --years 2024 --full-telemetry --skip-embeddings
```

### 3d. (Optional) FIA stewards' decisions via Docling

```bash
mkdir -p backend/fia_pdfs
# drop a few PDFs from https://www.fia.com/documents in there, then:
python -m ingestion.fia_parser backend/fia_pdfs/
```

---

## 4. Verify

```bash
python -m ingestion.status
```

Should print something like:
```
APEX ingestion status
==========================================================================
  2019  [######################..]  21 races |  6,840 laps |  340 pits |     0 telemetry |   84 embeds
  2020  [#################.......]  17 races |  5,820 laps |  290 pits |     0 telemetry |   68 embeds
  ...
```

Or hit the API:
```bash
uvicorn main:app --reload --port 8000 &
curl -s http://localhost:8000/stats | python -m json.tool | head -30
curl -s http://localhost:8000/health
```

---

## 5. Run the app

Two terminals:

```bash
# Terminal 1 - backend
cd backend && source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
npm install   # one-time
npm run dev
```

Open <http://localhost:5173>. You should land on the new Home page, with the
scale strip showing real numbers from your ingested data.

---

## 6. Run the test suite (no DB or IBM keys required)

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

Should print **18 passed**.

---

## 7. Back-up / share the data

Once everything's ingested, snapshot the DB so you don't have to re-run
Ergast on demo day:

```bash
python -m ingestion.export --out apex_dump.json
# or, smaller file:
python -m ingestion.export --out apex_dump.json --skip-telemetry
```

Restore on another machine: re-run steps 1-2 (creates the schema), then load
the JSON dump however you prefer (Supabase Studio's table editor or a small
Python script - the format is one top-level key per table, each value a list
of rows).

---

## Troubleshooting cheat sheet

| Symptom | Fix |
|---------|-----|
| `relation "vector" does not exist` | Enable pgvector in Supabase dashboard (step 0.1). |
| `FATAL: too many connections for role "postgres"` | Drop `--parallel-years` to 1 or 2; close idle Studio tabs. |
| Ergast `HTTP 429` repeatedly | Slow down. The script auto-retries with backoff but if it keeps failing, run one year at a time. |
| `Failed to load session` from FastF1 | First telemetry run downloads a 50 MB cache to `backend/fastf1_cache/`. Let it finish, re-run. |
| Granite returns 401 | Check `IBM_API_KEY`, restart the backend (token cache stale). |
| Frontend stuck on "sample" source pill | Backend not running on port 8000 or it can't reach Supabase. |
| `bad encoding` in psycopg2 | The Supabase URL needs to be URL-encoded if your password has special chars (`@`, `:`, `?`). Wrap in quotes. |
| `Glory Path` returns "No interventions" | The driver code didn't appear in that race. Try a different code (HAM, VER, NOR). |
| Counterfactual returns `Race not found` | Hit `/races` to see valid IDs first. |

---

## Quick TL;DR for the next time you sit down

```bash
cd ~/path/to/testFork
git checkout claude/analyze-project-jBgIH
git pull

# Terminal 1
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

Open <http://localhost:5173>.
