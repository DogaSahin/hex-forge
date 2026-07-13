from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app
from app.modules.maps.geometry import clamp_hp


def test_clamp_hp():
    assert clamp_hp(120, 100) == 100
    assert clamp_hp(-5, 100) == 0
    assert clamp_hp(30, 0) == 30  # no max => floor at 0 only


def _token(client):
    # Route by name (not the last delete-link in the list) — the shared test
    # campaign accumulates maps from earlier test modules in the same run, so
    # "last in the list" is not reliably "the one this test just created".
    client.post("/map", data={"name": "EditMenuMap"})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    mid = int(re.search(r'hx-get="/map/(\d+)"[^>]*>EditMenuMap</a>', txt).group(1))
    client.post(f"/map/{mid}/token", data={"name": "Old"})
    tokens = client.get(f"/map/{mid}/state").json()["tokens"]
    tid = next(t["id"] for t in tokens if t["name"] == "Old")
    return mid, tid


def test_edit_and_delete_token():
    client = TestClient(create_app())
    mid, tid = _token(client)
    client.post(
        f"/token/{tid}",
        data={
            "name": "New",
            "size": "3",
            "visible_to_players": "",
            "hp_current": "150",
            "hp_max": "100",
        },
    )
    t = client.get(f"/map/{mid}/state").json()["tokens"][0]
    assert t["name"] == "New"
    assert t["size"] == 3
    assert t["visible_to_players"] is False
    assert t["hp_current"] == 100  # clamped to max

    client.post(f"/token/{tid}/delete")
    assert client.get(f"/map/{mid}/state").json()["tokens"] == []
