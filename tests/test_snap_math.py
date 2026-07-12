from __future__ import annotations

from app.modules.maps.geometry import snap_to_grid


def test_snaps_to_nearest_intersection():
    # size 70, no offset: 100 -> 70 (nearest of 70/140), 120 -> 140
    assert snap_to_grid(100, 120, 70, 0, 0) == (70, 140)


def test_offset_respected():
    # offset 10: intersections at 10, 80, 150 ...; 95 -> 80, 130 -> 150
    assert snap_to_grid(95, 130, 70, 10, 10) == (80, 150)


def test_zero_size_returns_input():
    assert snap_to_grid(33, 44, 0, 0, 0) == (33, 44)


def test_half_cell_rounds_up_matching_js_math_round():
    # Exact half-cell input: (35-0)/70 = 0.5. JS Math.round(0.5) == 1 -> 70.
    # Python's banker's round(0.5) would give 0; half-up must match the JS mirror.
    assert snap_to_grid(35, 105, 70, 0, 0) == (70, 140)
