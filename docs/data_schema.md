# Data Schema

The initial schema follows the technical foundation document and adds `scenarios` so saved what-if changes have a first-class table.

## Core Entities

- `circuits`: circuit metadata plus normalized GPS path.
- `drivers`: Ergast driver identity and code.
- `constructors`: constructor identity.
- `seasons`: F1 season years.
- `races`: season rounds connected to circuits.
- `race_results`: grid, final position, points, and status.
- `lap_times`: lap-by-lap position and timing.
- `pit_stops`: stop timing and tire transitions.
- `safety_cars`: safety car and VSC windows.
- `telemetry_paths`: per-driver, per-lap normalized path samples.
- `race_embeddings`: text chunks and pgvector embeddings for RAG.
- `scenarios`: user-saved counterfactual changes.

## Migration Flow

From `backend/`:

```powershell
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

