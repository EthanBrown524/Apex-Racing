# APEX Racing Records

APEX is a Formula 1 race intelligence app for replaying historical races, testing counterfactual strategy changes, and forecasting upcoming events.

## Architecture

- Backend: FastAPI, SQLAlchemy, PostgreSQL, pgvector
- Frontend: React, Vite, Axios, Recharts
- Data: Ergast/OpenF1/FastF1 plus manually collected FIA PDFs
- AI: IBM Granite via watsonx.ai, with RAG context from PostgreSQL/pgvector

## Current Status

This repository has the initial project foundation:

- backend package structure
- database connection and ORM models
- first API routers
- ingestion starter modules
- Vite-style frontend source skeleton
- architecture and schema docs

## Local Setup

Create a local `.env` from `.env.example`, then install dependencies.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

