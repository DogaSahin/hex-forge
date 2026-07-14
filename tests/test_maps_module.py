from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.server import create_app


def test_maps_in_nav_and_index_renders():
    client = TestClient(create_app())
    r = client.get("/map")
    assert r.status_code == 200
    assert "Maps" in r.text  # nav label + page heading
