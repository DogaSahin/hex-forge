from __future__ import annotations

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
    assert segment_distance(dx, dy, 5, rule) == expected


def test_segment_negative_deltas():
    """Negative deltas are absorbed by abs(); results match positive equivalents."""
    # euclidean: (-3, 4) → abs: (3, 4) → sqrt(9+16)=5 → round(5)=5 → 5*5=25
    assert segment_distance(-3, 4, 5, "euclidean") == 25
    # chebyshev: (-4, -2) → abs: (4, 2) → max(4,2)=4 → 4*5=20
    assert segment_distance(-4, -2, 5, "chebyshev") == 20
    # five_ten_five: (-4, 2) → abs: (4, 2) → (4+2//2)*5=(4+1)*5=25
    assert segment_distance(-4, 2, 5, "five_ten_five") == 25
    # manhattan: (3, -2) → abs: (3, 2) → (3+2)*5=25
    assert segment_distance(3, -2, 5, "manhattan") == 25


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


def test_path_distance_backward_leg():
    """Negative deltas in path legs (x or y decreasing) are handled by abs()."""
    # 70px grid, chebyshev, feet=5
    # leg1: (140,0) to (0,0) → dx=abs(0-140)=140, dy=abs(0-0)=0 → 140//70=2 squares → 2*5=10 ft
    # leg2: (0,0) to (0,70) → dx=abs(0-0)=0, dy=abs(70-0)=70 → 70//70=1 square → 1*5=5 ft
    # total = 10 + 5 = 15
    pts = [(140, 0), (0, 0), (0, 70)]
    assert path_distance(pts, 5, "chebyshev", 70) == 15
