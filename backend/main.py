import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import (
    circuits,
    commentary,
    counterfactual,
    forecast,
    glory_path,
    races,
    scenarios,
)
from db.connection import dispose_engine


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        dispose_engine()


app = FastAPI(title="APEX Racing Records API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(races.router)
app.include_router(circuits.router)
app.include_router(counterfactual.router)
app.include_router(forecast.router)
app.include_router(scenarios.router)
app.include_router(glory_path.router)
app.include_router(commentary.router)


@app.get("/")
def health_check() -> dict:
    return {"status": "ok"}

