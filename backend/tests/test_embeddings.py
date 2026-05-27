"""Pure-function tests for ai.embeddings - no IBM credentials required.

embed_text / embed_texts hit IBM watsonx when credentials are present; with
credentials absent they fall back to a deterministic hash embedding. These
tests force the fallback so they run anywhere.
"""

import math

import pytest

from ai import embeddings


@pytest.fixture(autouse=True)
def _force_no_granite(no_granite):
    """Re-export the shared fixture as autouse for this module."""
    return no_granite


def test_pad_or_trim_passes_through_correct_length():
    vec = [0.1, 0.2, 0.3]
    assert embeddings._pad_or_trim(vec, 3) == vec


def test_pad_or_trim_pads_with_zeros():
    out = embeddings._pad_or_trim([1.0, 2.0], 5)
    assert out == [1.0, 2.0, 0.0, 0.0, 0.0]


def test_pad_or_trim_trims_to_target():
    out = embeddings._pad_or_trim([1.0, 2.0, 3.0, 4.0, 5.0], 3)
    assert out == [1.0, 2.0, 3.0]


def test_hash_embed_is_deterministic():
    a = embeddings._hash_embed("the quick brown fox", 128)
    b = embeddings._hash_embed("the quick brown fox", 128)
    assert a == b


def test_hash_embed_distinguishes_different_inputs():
    a = embeddings._hash_embed("hamilton wins", 128)
    b = embeddings._hash_embed("verstappen wins", 128)
    assert a != b


def test_hash_embed_is_unit_normalised():
    vec = embeddings._hash_embed("monaco grand prix", 256)
    norm = math.sqrt(sum(v * v for v in vec))
    assert 0.99 <= norm <= 1.01


def test_hash_embed_handles_empty_string():
    vec = embeddings._hash_embed("", 64)
    assert len(vec) == 64
    assert all(v == 0.0 for v in vec)


def test_cosine_identical_vectors_returns_one():
    vec = [1.0, 2.0, 3.0]
    assert pytest.approx(embeddings.cosine(vec, vec), abs=1e-9) == 1.0


def test_cosine_orthogonal_vectors_returns_zero():
    assert embeddings.cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_handles_empty_vectors():
    assert embeddings.cosine([], []) == 0.0
    assert embeddings.cosine([], [1.0, 2.0]) == 0.0


def test_cosine_truncates_to_shorter_vector():
    assert embeddings.cosine([1.0, 0.0, 99.0], [1.0, 0.0]) > 0.99


def test_chunk_text_returns_empty_for_empty_input():
    assert embeddings.chunk_text("") == []


def test_chunk_text_returns_single_chunk_for_short_input():
    chunks = list(embeddings.chunk_text("short text", chunk_size=100, overlap=20))
    assert chunks == ["short text"]


def test_chunk_text_overlaps_when_text_exceeds_chunk_size():
    text = "x" * 1000
    chunks = list(embeddings.chunk_text(text, chunk_size=400, overlap=50))
    assert len(chunks) >= 2
    # Adjacent chunks should share the overlap window
    for chunk in chunks:
        assert len(chunk) <= 400


def test_embed_texts_falls_back_to_hash_without_credentials():
    out = embeddings.embed_texts(["hello", "world"], target_dim=128)
    assert len(out) == 2
    assert all(len(vec) == 128 for vec in out)
    assert out[0] != out[1]


def test_embed_texts_empty_input_returns_empty():
    assert embeddings.embed_texts([]) == []


def test_embed_text_returns_single_vector_with_target_dim():
    out = embeddings.embed_text("monza tifosi", target_dim=64)
    assert len(out) == 64
