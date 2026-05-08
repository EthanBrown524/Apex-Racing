# APEX Architecture

APEX is organized into five layers:

1. Data sources: Ergast, FastF1, OpenF1, and FIA PDFs.
2. Ingestion: Python loaders normalize external data and write to PostgreSQL.
3. Database: PostgreSQL stores race records, lap timing, telemetry paths, scenarios, and vector embeddings.
4. AI layer: Granite and RAG modules generate explanations, counterfactual narratives, and forecast context.
5. Product surface: FastAPI exposes stable endpoints consumed by the React frontend.

The frontend never calls AI services directly. It only talks to FastAPI.

## Development Priorities

1. Backend schema, DB connection, and first race endpoints.
2. Ergast ingestion for 2023 metadata, then results, laps, and pit stops.
3. Track canvas replay using normalized circuit paths.
4. Counterfactual simulation contract.
5. Forecast dashboard and RAG-backed explanations.

