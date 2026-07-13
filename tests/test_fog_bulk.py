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


def _map_with_fog(client, name):
    mid = _make_map(client, name)
    client.post(
        f"/map/{mid}/fog",
        data={
            "op": "reveal",
            "geom": json.dumps({"type": "rect", "x": 0, "y": 0, "w": 70, "h": 70}),
        },
    )
    return mid


def test_reveal_all_reduces_to_single_all():
    client = TestClient(create_app())
    mid = _map_with_fog(client, "BulkMapReveal")
    r = client.post(f"/map/{mid}/fog/reveal-all")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    fog = client.get(f"/map/{mid}/state").json()["fog"]
    assert fog == [{"op": "reveal", "geom": {"type": "all"}}]


def test_hide_all_empties():
    client = TestClient(create_app())
    mid = _map_with_fog(client, "BulkMapHide")
    r = client.post(f"/map/{mid}/fog/hide-all")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert client.get(f"/map/{mid}/state").json()["fog"] == []
