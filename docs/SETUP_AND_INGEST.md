# APEX Setup & Ingestion Runbook

Run these top-to-bottom the first time you set the project up. After that, only the **"Run it"** section matters day-to-day.

Assumes Windows (PowerShell) primary, with Bash equivalents shown. Adjust paths if your project lives elsewhere.

---

## 0. Prerequisites (install once)

| Tool | Why | How |
|------|-----|-----|
| Python 3.11+ | Backend | https://www.python.org/downloads/ |
| Node 18+ | Frontend | https://nodejs.org/ |
| PostgreSQL 15+ | Database | https://www.postgresql.org/download/ |
| pgvector extension | RAG vector search | See step 2 |
| Git | Version control | https://git-scm.com/ |

Optional but recommended:
- **DBeaver** or **pgAdmin** to inspect the database
- **Docker Desktop** if you prefer running Postgres in a container instead of native

---

## 1. Clone & branch

```powershell
git clone https://github.com/CWAGAdmin/testFork.git
cd testFork
git checkout claude/analyze-project-jBgIH
```

---

## 2. PostgreSQL setup

### 2a. Create the database

```powershell
# Default Windows install:
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE apex;"
```

Bash:
```bash
psql -U postgres -c "CREATE DATABASE apex;"
```

### 2b. Install pgvector

Pick **one** of these.

**Option A - Stack Builder (Windows, easiest):**
1. Run `Stack Builder` (came with Postgres install)
2. Pick your installed Postgres
3. Categories -> Spatial Extensions -> install `pgvector`
4. Done.

**Option B - From source (any OS):**
```bash
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**Option C - Docker shortcut (skip native Postgres entirely):**
```powershell
docker run -d --name apex-pg `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=apex `
  -p 5432:5432 `
  pgvector/pgvector:pg16
```

### 2c. Enable the extension on your database

```powershell
psql -U postgres -d apex -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Verify:
```powershell
psql -U postgres -d apex -c "SELECT extname FROM pg_extension WHERE extname='vector';"
# Should print: vector
```

---

## 3. Environment file

```powershell
copy .env.example .env
notepad .env
```

Set at minimum:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/apex
FRONTEND_URL=http://localhost:5173
```

Optional (Granite explanations + real embeddings - the app still runs without these, just with the hash-vector fallback):
```
IBM_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Get the IBM keys here:
- API key: https://cloud.ibm.com/iam/apikeys
- Project ID: https://dataplatform.cloud.ibm.com/projects (open a project, look in Manage tab)

---

## 4. Backend install

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Bash:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Run database migrations

From `backend/` with the venv active:
```powershell
alembic upgrade head
```

Verify the 11 tables exist:
```powershell
psql -U postgres -d apex -c "\dt"
# Should list: circuits, drivers, constructors, seasons, races, race_results,
# lap_times, pit_stops, safety_cars, telemetry_paths, race_embeddings, scenarios
```

---

## 6. Ingest the 2019-2024 data

**This is the long part.** Expect 30-90 minutes total depending on network + FastF1 cache state. The script is restart-safe - just re-run if it dies. `run_bulk.py` shows tqdm progress bars and prints a totals table at the end.

### 6a. Quick path (metadata + results + laps + pits, no telemetry)

Fastest way to get a usable demo. Takes ~10-20 min total.

```powershell
cd backend
python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024 --skip-telemetry --skip-embeddings
```

### 6b. Faster path (run multiple seasons in parallel)

If you have RAM + network bandwidth, ingest several seasons at once. Takes ~5-10 min.

```powershell
python -m ingestion.run_bulk --years 2019 2020 2021 2022 2023 2024 --skip-telemetry --skip-embeddings --parallel-years 3
```

`--parallel-years N` spins up N worker processes; each handles one season. Three is a safe ceiling on most laptops; the Ergast API rate-limits aggressively so going higher won't help.

### 6c. Add embeddings for AI/RAG (recommended for hackathon demo)

```powershell
python -m ingestion.embed_races --years 2019 2020 2021 2022 2023 2024
```

### 6d. (Optional, slow) Add telemetry for animated car positions

Pulls per-driver per-lap x/y/speed paths via FastF1. Each race ~1-3 min sampled, ~5-15 min for `--full-telemetry`.

```powershell
python -m ingestion.run_bulk --years 2023 2024 --skip-embeddings
# Every lap (slow but cinematic):
python -m ingestion.run_bulk --years 2024 --full-telemetry --skip-embeddings
```

(Just the most recent two seasons keeps the demo cinematic without waiting an hour.)

### 6e. (Optional) FIA stewards' decisions via Docling

Download the curated official FIA PDF manifest:

```powershell
python -m ingestion.fia_sources download
```

Then ingest the downloaded PDFs into the RAG index:

```powershell
python -m ingestion.fia_sources ingest
```

Or do both in one command:

```powershell
python -m ingestion.fia_sources all
```

If you only have one PDF for one race:
```powershell
python -m ingestion.fia_parser backend/fia_pdfs/decision_47.pdf --race-id 42 --title "Decision 47 - Verstappen"
```

### 6f. Check progress at any time

```powershell
python -m ingestion.status
```

Prints something like:
```
  2019  [##########..............]  10 races |  3,254 laps |  178 pits |  840 telemetry |   40 embeds
  2020  [#####################...]  17 races |  6,201 laps |  290 pits | 1,520 telemetry |   68 embeds
  ...
```

### 6g. Backup / share the data

Ingesting takes a while. Once it's done, dump the DB to JSON so you can restore on the demo laptop without re-running FastF1:

```powershell
python -m ingestion.export --out apex_dump.json
# or skip telemetry to keep the file small:
python -m ingestion.export --out apex_dump.json --skip-telemetry
```

---

## 7. Per-year commands (if you'd rather do it one year at a time)

```powershell
# 2019
python -m ingestion.run_bulk --years 2019 --skip-telemetry --skip-embeddings
python -m ingestion.embed_races --years 2019

# 2020
python -m ingestion.run_bulk --years 2020 --skip-telemetry --skip-embeddings
python -m ingestion.embed_races --years 2020

# 2021
python -m ingestion.run_bulk --years 2021 --skip-telemetry --skip-embeddings
python -m ingestion.embed_races --years 2021

# 2022
python -m ingestion.run_bulk --years 2022 --skip-telemetry --skip-embeddings
python -m ingestion.embed_races --years 2022

# 2023 (with telemetry)
python -m ingestion.run_bulk --years 2023 --skip-embeddings
python -m ingestion.embed_races --years 2023

# 2024 (with telemetry)
python -m ingestion.run_bulk --years 2024 --skip-embeddings
python -m ingestion.embed_races --years 2024
```

---

## 8. Frontend install (one-time)

In a **second terminal**:
```powershell
cd frontend
npm install
```

---

## 9. Run it

Two terminals running side-by-side.

**Terminal 1 - backend** (from `backend/` with venv active):
```powershell
uvicorn main:app --reload --port 8000
```

**Terminal 2 - frontend** (from `frontend/`):
```powershell
npm run dev
```

Then open:
- App: http://localhost:5173
- API docs: http://localhost:8000/docs

---

## 10. Verify ingestion worked

```powershell
psql -U postgres -d apex -c "SELECT season_year, COUNT(*) FROM races GROUP BY season_year ORDER BY season_year;"
```
Should show roughly 21-22 rows for 2019-2023, 24 for 2024.

```powershell
psql -U postgres -d apex -c "SELECT COUNT(*) FROM lap_times;"
```
Should be 200,000+ once a few seasons are ingested.

```powershell
psql -U postgres -d apex -c "SELECT COUNT(*) FROM race_embeddings;"
```
Should be roughly `races * 4` after `embed_races` runs.

```powershell
psql -U postgres -d apex -c "SELECT metadata->>'source', COUNT(*) FROM race_embeddings GROUP BY 1;"
```
Should show `race_narrative` and (if you ingested FIA PDFs) `fia_decision`.

---

## 11. Quick API smoke tests

```powershell
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/races
curl http://localhost:8000/forecast/1
curl http://localhost:8000/showcase
curl -X POST http://localhost:8000/glory-path/solve `
  -H "Content-Type: application/json" `
  -d '{\"race_id\": 1, \"driver_code\": \"HAM\", \"target_position\": 1}'
curl -X POST http://localhost:8000/championship/impact `
  -H "Content-Type: application/json" `
  -d '{\"race_id\": 1, \"changes\": [{\"driver_code\": \"VER\", \"change_type\": \"dnf\", \"lap\": 10}]}'
```

### Engine unit tests (no DB, no IBM keys)

```powershell
cd backend
.\.venv\Scripts\activate
pytest tests/ -v
```

Should print **18 passed**. These cover the change helpers, the
counterfactual engine's pure logic, the realism heuristic, and the showcase
scenario schema.

---

## 12. Common issues

| Symptom | Fix |
|---------|-----|
| `relation "vector" does not exist` | Step 2c - `CREATE EXTENSION vector` |
| `psycopg2 ImportError` on Windows | `pip install psycopg2-binary` (already in requirements.txt) |
| Ergast rate limits (HTTP 429) | The script auto-retries with backoff; just wait, it'll resume |
| FastF1 errors `Failed to load session` | First run downloads ~50MB cache to `backend/fastf1_cache/`; let it finish, re-run |
| Granite returns 401 | Check `IBM_API_KEY` env var; the cached token may be stale - restart the backend |
| Frontend shows "sample" source pill | Backend not running OR no races in DB - re-check step 5 + 6 |
| `npm run dev` shows port conflict | Vite picks a new port automatically; check terminal output |
| Glory Path returns "No interventions" | The driver code didn't match anyone in that race - try a different code (HAM, VER, NOR, etc.) |
| Counterfactual `Race not found` | The race_id in your request doesn't exist - hit `/races` first to see valid IDs |

---

## 13. Resetting everything

If you want to start over from scratch:

```powershell
# Drop and recreate
psql -U postgres -c "DROP DATABASE apex;"
psql -U postgres -c "CREATE DATABASE apex;"
psql -U postgres -d apex -c "CREATE EXTENSION vector;"

# Re-migrate
cd backend
.\.venv\Scripts\activate
alembic upgrade head

# Re-ingest (see step 6)
```

To delete just the embeddings (e.g. to re-embed with different credentials):
```powershell
psql -U postgres -d apex -c "TRUNCATE race_embeddings;"
python -m ingestion.embed_races --years 2019 2020 2021 2022 2023 2024
```

To delete one race's data without nuking everything:
```sql
DELETE FROM telemetry_paths WHERE race_id = 42;
DELETE FROM lap_times       WHERE race_id = 42;
DELETE FROM pit_stops       WHERE race_id = 42;
DELETE FROM race_results    WHERE race_id = 42;
DELETE FROM race_embeddings WHERE race_id = 42;
DELETE FROM races           WHERE id = 42;
```

---

## 14. TL;DR for a returning user

You already set everything up once and just want to run the app today:

```powershell
# Terminal 1
cd backend
.\.venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

Open http://localhost:5173 and go.
