from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def _make_map(client):
    client.post("/map", data={"name": "Token Map"})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    return int(re.findall(r"/map/(\d+)/delete", txt)[-1])


def test_create_disc_token_appears_in_state():
    client = TestClient(create_app())
    mid = _make_map(client)
    client.post(
        f"/map/{mid}/token",
        data={
            "name": "Goblin",
            "kind": "disc",
            "color": "#c0392b",
            "size": "1",
            "layer": "tokens",
        },
    )
    tokens = client.get(f"/map/{mid}/state").json()["tokens"]
    assert len(tokens) == 1
    assert tokens[0]["name"] == "Goblin"
    assert tokens[0]["color"] == "#c0392b"
    assert tokens[0]["layer"] == "tokens"
