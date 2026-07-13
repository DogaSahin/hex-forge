from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def test_server_snaps_when_flagged():
    client = TestClient(create_app())
    name = "Token Snap Route Map"
    client.post("/map", data={"name": name})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    m = re.search(rf'/map/(\d+)"[^>]*>{re.escape(name)}<', txt)
    assert m is not None
    mid = int(m.group(1))
    client.post(f"/map/{mid}/token", data={"name": "T"})
    tid = client.get(f"/map/{mid}/state").json()["tokens"][0]["id"]
    # grid 70, raw 100,120 -> snapped 70,140
    client.post(f"/token/{tid}/move", data={"x": "100", "y": "120", "snap": "1"})
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert (t["x"], t["y"]) == (70, 140)
