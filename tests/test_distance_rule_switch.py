from __future__ import annotations

from app.modules.maps.distance import segment_distance


def test_same_move_differs_by_rule():
    # Same geometry (dx=4, dy=2 squares, feet=5) must yield different totals depending
    # on the per-map diagonal rule -- this is what makes the rule selector meaningful.
    dx, dy, feet = 4, 2, 5
    results = {
        r: segment_distance(dx, dy, feet, r)
        for r in ("chebyshev", "five_ten_five", "euclidean", "manhattan")
    }
    assert results["chebyshev"] == 20
    assert results["five_ten_five"] == 25
    assert results["euclidean"] == 20
    assert results["manhattan"] == 30
    # all four should not collapse to one value
    assert len(set(results.values())) >= 3
