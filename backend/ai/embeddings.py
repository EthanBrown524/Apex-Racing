"""IBM watsonx.ai embeddings client used for RAG over race narratives + FIA docs."""

from __future__ import annotations

import math
import os
from typing import Iterable

import httpx
from dotenv import load_dotenv

from ai.granite import get_access_token

load_dotenv()

WATSONX_VERSION = "2024-05-31"
EMBED_MODEL_ID = "ibm/slate-30m-english-rtrvr"
EMBED_DIM = 384  # matches slate-30m
LEGACY_DIM = 1536  # RaceEmbedding.embedding column is Vector(1536)


def _pad_or_trim(vec: list[float], target: int) -> list[float]:
    if len(vec) == target:
        return vec
    if len(vec) > target:
        return vec[:target]
    return vec + [0.0] * (target - len(vec))


def embed_texts(texts: list[str], target_dim: int = LEGACY_DIM) -> list[list[float]]:
    """Embed a batch of strings via watsonx. Falls back to a deterministic
    hash-based vector when IBM credentials are missing so RAG still works locally."""
    if not texts:
        return []

    api_key = os.getenv("IBM_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    if not api_key or not project_id:
        return [_hash_embed(t, target_dim) for t in texts]

    try:
        watsonx_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        url = f"{watsonx_url}/ml/v1/text/embeddings?version={WATSONX_VERSION}"
        token = get_access_token()

        payload = {
            "model_id": EMBED_MODEL_ID,
            "project_id": project_id,
            "inputs": texts,
        }

        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        vectors = [item.get("embedding", []) for item in results]
        return [_pad_or_trim(v, target_dim) for v in vectors]
    except Exception:
        return [_hash_embed(t, target_dim) for t in texts]


def embed_text(text: str, target_dim: int = LEGACY_DIM) -> list[float]:
    return embed_texts([text], target_dim)[0]


def _hash_embed(text: str, dim: int) -> list[float]:
    """Deterministic fallback so RAG still functions without IBM creds.
    Distributes character n-gram hashes into a fixed-dim float vector."""
    vec = [0.0] * dim
    if not text:
        return vec
    cleaned = text.lower()
    for i in range(len(cleaned) - 2):
        tri = cleaned[i : i + 3]
        h = (hash(tri) & 0x7FFFFFFF) % dim
        vec[h] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(a[i] * a[i] for i in range(n))) or 1.0
    nb = math.sqrt(sum(b[i] * b[i] for i in range(n))) or 1.0
    return dot / (na * nb)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> Iterable[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]
