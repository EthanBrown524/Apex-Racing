# Smoke tests

Lightweight engine tests that don't require Postgres or watsonx. They verify
the pure-Python pieces of the simulation pipeline.

```bash
cd backend
pytest tests/ -v
```

Tests that need DB or IBM credentials are skipped automatically when their
environment isn't present.
