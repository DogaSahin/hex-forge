from __future__ import annotations

import math


def segment_distance(dx: int, dy: int, feet: int, rule: str) -> int:
    """Distance in feet for a move of |dx|,|dy| squares under the given diagonal rule.

    Args:
        dx: change in x (squares), will be abs'd
        dy: change in y (squares), will be abs'd
        feet: distance scale (feet per square)
        rule: one of "chebyshev", "five_ten_five", "euclidean", "manhattan",
            or unknown (defaults to chebyshev)

    Returns:
        Distance in feet (int)
    """
    dx, dy = abs(dx), abs(dy)
    hi, lo = max(dx, dy), min(dx, dy)
    if rule == "chebyshev":
        return hi * feet
    if rule == "five_ten_five":
        return (hi + lo // 2) * feet
    if rule == "euclidean":
        return round(math.sqrt(dx * dx + dy * dy)) * feet
    if rule == "manhattan":
        return (dx + dy) * feet
    return hi * feet  # default to chebyshev


def path_distance(points: list[tuple[int, int]], feet: int, rule: str, grid_size: int) -> int:
    """Sum of segment distances along a polyline of pixel points.

    Args:
        points: list of (x_px, y_px) pixel coordinates
        feet: distance scale (feet per square)
        rule: diagonal rule ("chebyshev", "five_ten_five", "euclidean", "manhattan")
        grid_size: pixels per square

    Returns:
        Total distance in feet (int). Returns 0 if grid_size <= 0 or fewer than 2 points.
    """
    if grid_size <= 0 or len(points) < 2:
        return 0
    total = 0
    for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False):
        dx = round(abs(x1 - x0) / grid_size)
        dy = round(abs(y1 - y0) / grid_size)
        total += segment_distance(dx, dy, feet, rule)
    return total
