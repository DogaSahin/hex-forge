from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.server import create_app


def _make_map(client):
    client.post("/map", data={"name": "Editor Map"})
    txt = client.get("/map", headers={"HX-Request": "true"}).text
    return int(re.findall(r"/map/(\d+)/delete", txt)[-1])


def test_editor_fragment_has_stage_host():
    client = TestClient(create_app())
    mid = _make_map(client)
    r = client.get(f"/map/{mid}")
    assert r.status_code == 200
    assert f'data-map-id="{mid}"' in r.text
    assert 'id="map-stage"' in r.text


def test_state_shape():
    client = TestClient(create_app())
    mid = _make_map(client)
    state = client.get(f"/map/{mid}/state").json()
    assert state["map"]["id"] == mid
    assert state["tokens"] == []
    assert state["fog"] == []
