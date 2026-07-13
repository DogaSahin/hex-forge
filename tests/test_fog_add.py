from __future__ import annotations

import json
import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def _make_map(client, name):
    client.post("/map", data={"name": name})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    m = re.search(rf'/map/(\d+)"[^>]*>{re.escape(name)}<', txt)
    assert m is not None
    return int(m.group(1))


def test_rectangle_reveal_persists():
    client = TestClient(create_app())
    mid = _make_map(client, "FogMap")
    geom = json.dumps({"type": "rect", "x": 0, "y": 0, "w": 140, "h": 140})
    r = client.post(f"/map/{mid}/fog", data={"op": "reveal", "geom": geom})
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    fog = client.get(f"/map/{mid}/state").json()["fog"]
    assert fog == [{"op": "reveal", "geom": {"type": "rect", "x": 0, "y": 0, "w": 140, "h": 140}}]


def test_malformed_geom_rejected_without_500():
    client = TestClient(create_app())
    mid = _make_map(client, "FogMapBadGeom")
    r = client.post(f"/map/{mid}/fog", data={"op": "reveal", "geom": "not json"})
    assert r.status_code == 200
    assert r.json() == {"ok": False}
    fog = client.get(f"/map/{mid}/state").json()["fog"]
    assert fog == []
