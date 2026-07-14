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


def test_hide_after_reveal_kept_in_order():
    client = TestClient(create_app())
    mid = _make_map(client, "HideMap")
    client.post(
        f"/map/{mid}/fog",
        data={
            "op": "reveal",
            "geom": json.dumps({"type": "rect", "x": 0, "y": 0, "w": 140, "h": 140}),
        },
    )
    client.post(
        f"/map/{mid}/fog",
        data={
            "op": "hide",
            "geom": json.dumps({"type": "rect", "x": 0, "y": 0, "w": 70, "h": 70}),
        },
    )
    fog = client.get(f"/map/{mid}/state").json()["fog"]
    assert [e["op"] for e in fog] == ["reveal", "hide"]
