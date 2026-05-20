"""Coordinate normalization helpers for ingestion.

Used by fastf1_loader and run_telemetry to map raw x/y telemetry into the
0..1 box that the frontend canvas renders against.
"""

from __future__ import annotations


def normalize_points(points: list[dict], x_key: str = "x", y_key: str = "y") -> list[dict]:
    if not points:
        return []

    xs = [point[x_key] for point in points]
    ys = [point[y_key] for point in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = (x_max - x_min) or 1
    y_span = (y_max - y_min) or 1

    return [
        {
            **point,
            "x": (point[x_key] - x_min) / x_span,
            "y": (point[y_key] - y_min) / y_span,
        }
        for point in points
    ]
