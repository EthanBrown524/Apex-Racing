"""Shared pytest fixtures for the APEX test suite.

The `no_granite` fixture strips IBM credentials from the environment so any
test that incidentally hits the watsonx codepaths uses the deterministic
fallbacks (hash embeddings, heuristic realism, etc.). Apply it explicitly per
test - it is NOT autouse, so DB/Granite-aware tests can opt in selectively.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def no_granite(monkeypatch):
    """Force Granite to be unavailable so heuristic / fallback paths run."""
    monkeypatch.delenv("IBM_API_KEY", raising=False)
    monkeypatch.delenv("WATSONX_PROJECT_ID", raising=False)
    return monkeypatch
