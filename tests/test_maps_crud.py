from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.server import create_app


def test_create_and_delete_map():
    client = TestClient(create_app())
    r = client.post("/map", data={"name": "Sunless Citadel"})
    assert r.status_code == 200
    assert "Sunless Citadel" in r.text

    # find the id from the list markup
    r = client.get("/map", headers={"HX-Request": "true"})
    assert "Sunless Citadel" in r.text

    # delete every map, list should end empty of that name
    # (parse id via the delete form action)
    import re

    ids = re.findall(r"/map/(\d+)/delete", r.text)
    assert ids
    for mid in ids:
        client.post(f"/map/{mid}/delete")
    r = client.get("/map", headers={"HX-Request": "true"})
    assert "Sunless Citadel" not in r.text


def test_create_blank_name_is_noop():
    client = TestClient(create_app())
    before = client.get("/map", headers={"HX-Request": "true"}).text
    client.post("/map", data={"name": "   "})
    after = client.get("/map", headers={"HX-Request": "true"}).text
    assert before.count("map-list-item") == after.count("map-list-item")
