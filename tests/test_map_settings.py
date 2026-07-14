from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def _make_map(client, name):
    client.post("/map", data={"name": name})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    m = re.search(rf'/map/(\d+)"[^>]*>{re.escape(name)}<', txt)
    assert m is not None
    return int(m.group(1))


def test_settings_persist():
    client = TestClient(create_app())
    mid = _make_map(client, "Grid Map Persist")
    client.post(
        f"/map/{mid}/settings",
        data={
            "grid_size_px": "50",
            "grid_offset_x": "5",
            "grid_offset_y": "7",
            "grid_visible": "on",
            "feet_per_square": "10",
            "diagonal_rule": "euclidean",
        },
    )
    state = client.get(f"/map/{mid}/state").json()["map"]
    assert state["grid_size_px"] == 50
    assert state["grid_offset_x"] == 5
    assert state["feet_per_square"] == 10
    assert state["diagonal_rule"] == "euclidean"
    assert state["grid_visible"] is True


def test_invalid_rule_ignored():
    client = TestClient(create_app())
    mid = _make_map(client, "Grid Map Invalid Rule")
    client.post(
        f"/map/{mid}/settings",
        data={
            "grid_size_px": "70",
            "grid_offset_x": "0",
            "grid_offset_y": "0",
            "feet_per_square": "5",
            "diagonal_rule": "nonsense",
        },
    )
    state = client.get(f"/map/{mid}/state").json()["map"]
    assert state["diagonal_rule"] == "chebyshev"  # unchanged
    assert state["grid_visible"] is False  # checkbox absent => off
