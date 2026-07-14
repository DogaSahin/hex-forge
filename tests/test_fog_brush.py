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


def test_path_reveal_persists():
    client = TestClient(create_app())
    mid = _make_map(client, "BrushMap")
    geom = json.dumps({"type": "path", "points": [0, 0, 70, 0, 70, 70]})
    client.post(f"/map/{mid}/fog", data={"op": "reveal", "geom": geom})
    fog = client.get(f"/map/{mid}/state").json()["fog"]
    assert fog[0]["geom"]["type"] == "path"
    assert fog[0]["geom"]["points"] == [0, 0, 70, 0, 70, 70]
