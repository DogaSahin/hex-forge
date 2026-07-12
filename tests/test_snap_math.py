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
