from __future__ import annotations

import math

import pytest

from app.modules.maps.distance import path_distance, segment_distance


@pytest.mark.parametrize(
    "dx,dy,rule,expected",
    [
        (3, 0, "chebyshev", 15),
        (3, 3, "chebyshev", 15),  # max(3,3)*5
        (4, 2, "chebyshev", 20),  # max*5
        (4, 2, "five_ten_five", 25),  # (4 + 2//2)*5 = (4+1)*5
        (3, 3, "five_ten_five", 20),  # (3 + 1)*5
        (3, 4, "euclidean", 25),  # round(5)*5
        (2, 2, "euclidean", 15),  # round(2.828)*5 = 3*5 = 15
        (3, 2, "manhattan", 25),  # (3+2)*5
    ],
)
def test_segment_rules(dx, dy, rule, expected):
    # recompute euclidean expectation explicitly to avoid table mistakes
    if rule == "euclidean":
        expected = round(math.sqrt(dx * dx + dy * dy)) * 5
    assert segment_distance(dx, dy, 5, rule) == expected


def test_segment_diagonal_chebyshev():
    """Pure diagonal case: chebyshev treats diagonal as same as horizontal/vertical."""
    assert segment_distance(5, 5, 10, "chebyshev") == 50


def test_segment_straight_manhattan():
    """Straight line case: manhattan sums the components."""
    assert segment_distance(0, 7, 10, "manhattan") == 70


def test_segment_unknown_rule_defaults_to_chebyshev():
    """Unknown rule falls back to chebyshev (hi * feet)."""
    assert segment_distance(3, 2, 5, "unknown") == 15


def test_path_distance_with_chebyshev():
    """pixels in px on a 70px grid: (0,0)->(140,0)->(140,140) = 2 + 2 squares."""
    # chebyshev: 2*5 + 2*5 = 20
    pts = [(0, 0), (140, 0), (140, 140)]
    assert path_distance(pts, 5, "chebyshev", 70) == 20


def test_path_distance_empty_points():
    """Fewer than 2 points returns 0."""
    assert path_distance([], 5, "chebyshev", 70) == 0
    assert path_distance([(0, 0)], 5, "chebyshev", 70) == 0


def test_path_distance_invalid_grid_size():
    """grid_size <= 0 returns 0."""
    pts = [(0, 0), (100, 100)]
    assert path_distance(pts, 5, "chebyshev", 0) == 0
    assert path_distance(pts, 5, "chebyshev", -10) == 0


def test_path_distance_multiple_segments():
    """Multiple segments: each leg is summed independently."""
    # 70px grid: (0,0)->(70,0) = 1 sq, (70,0)->(140,70) = 1 sq + 1 sq = chebyshev max = 1 sq
    # chebyshev(1, 0, feet=5) = 1*5 = 5
    # chebyshev(1, 1, feet=5) = 1*5 = 5
    # total = 5 + 5 = 10
    pts = [(0, 0), (70, 0), (140, 70)]
    assert path_distance(pts, 5, "chebyshev", 70) == 10
