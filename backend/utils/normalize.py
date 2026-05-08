def normalize_points(points: list[dict], x_key: str = "x", y_key: str = "y") -> list[dict]:
    if not points:
        return []

    xs = [point[x_key] for point in points]
    ys = [point[y_key] for point in points]
    x_span = max(xs) - min(xs) or 1
    y_span = max(ys) - min(ys) or 1

    return [
        {
            **point,
            "x": (point[x_key] - min(xs)) / x_span,
            "y": (point[y_key] - min(ys)) / y_span,
        }
        for point in points
    ]

