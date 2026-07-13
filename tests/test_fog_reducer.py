from __future__ import annotations

from app.modules.maps.fog import reduce_ops


def _rect(x, y, w, h):
    return {"type": "rect", "x": x, "y": y, "w": w, "h": h}


def test_reveal_all_collapses_priors():
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": _rect(0, 0, 35, 35)},
        {"op": "reveal", "geom": {"type": "all"}},
    ]
    out = reduce_ops(ops)
    assert out == [{"op": "reveal", "geom": {"type": "all"}}]


def test_hide_all_empties():
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": {"type": "all"}},
    ]
    assert reduce_ops(ops) == []


def test_normal_ops_preserved_in_order():
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": _rect(10, 10, 20, 20)},
    ]
    assert reduce_ops(ops) == ops


def test_reveal_after_hide_all_still_applies():
    """DM hides everything, then reveals one room — the reveal must survive."""
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": {"type": "all"}},
        {"op": "reveal", "geom": _rect(140, 140, 70, 70)},
    ]
    assert reduce_ops(ops) == [{"op": "reveal", "geom": _rect(140, 140, 70, 70)}]


def test_malformed_non_dict_geom_entry_is_skipped():
    """A bad row already in the DB (non-dict geom) must be skipped, not crash the reducer —
    later, well-formed ops still apply."""
    ops = [
        {"op": "reveal", "geom": 5},
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
    ]
    assert reduce_ops(ops) == [{"op": "reveal", "geom": _rect(0, 0, 70, 70)}]


def test_hide_after_reveal_all_still_applies():
    """DM reveals the whole map, then re-hides one room — the hide must survive."""
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "reveal", "geom": {"type": "all"}},
        {"op": "hide", "geom": _rect(210, 0, 70, 70)},
    ]
    assert reduce_ops(ops) == [
        {"op": "reveal", "geom": {"type": "all"}},
        {"op": "hide", "geom": _rect(210, 0, 70, 70)},
    ]
