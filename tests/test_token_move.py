from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def _map_with_token(client):
    client.post("/map", data={"name": "MoveMap"})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    mid = int(re.findall(r"/map/(\d+)/delete", txt)[-1])
    client.post(f"/map/{mid}/token", data={"name": "T"})
    tid = client.get(f"/map/{mid}/state").json()["tokens"][0]["id"]
    return mid, tid


def test_move_persists_position():
    client = TestClient(create_app())
    mid, tid = _map_with_token(client)
    r = client.post(f"/token/{tid}/move", data={"x": "245", "y": "310"})
    assert r.status_code == 200
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["x"] == 245
    assert t["y"] == 310
